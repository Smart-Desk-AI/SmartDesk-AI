import json
import logging
import smtplib
import asyncio
from typing import List, Optional, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.controllers.BaseController import BaseController 
from src.stores.llm.LLMEnums import DocumentTypeEnum
from src.stores.llm.templates.locales.en.rag import reformat_query_prompt
from src.models.db_schemas import Project, DataChunk, Conversation
from src.helpers.config import get_settings, Settings


class ConversationNLPController(BaseController):
    def __init__(self, db_client, generation_client, template_parser, vectordb_client, embedding_client):
        super().__init__()
        self.db_client = db_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.vectordb_client = vectordb_client
        self.logger = logging.getLogger('uvicorn.error')
        self.app_settings = Settings()

    def create_table_name(self, project_id: str) -> str:
        return f"collection_384_{project_id}".strip().lower()

    async def reformalize_conversation(self, project_id: int, query: str, history_messages: List) -> str:
        """
        Reformalize query to be standalone, but WITHOUT using chat history in the LLM call.
        The chat history can contaminate the reformulation.
        Instead, we manually extract context from history and inject it as instructions.
        """
        if not history_messages:
            return query

        # Extract last user query to understand context
        last_user_query = None
        for msg in reversed(history_messages):
            msg_role = msg.get("role", "").lower() if isinstance(msg, dict) else ""
            if msg_role in ["user", "human"]:
                last_user_query = msg.get("content", "").strip()
                break

        self.logger.info(f"reformalize_conversation: current='{query}' | previous='{last_user_query}'")

        # SIMPLE approach: Just return the query as-is if it's already standalone
        # Check if query already contains enough context clues
        context_words = ["what", "how", "when", "where", "which", "who", "shopify", "payment", "method"]
        has_context = any(word in query.lower() for word in context_words)
        
        if has_context and len(query) > 5:
            self.logger.info(f"Query is already standalone: '{query}'")
            return query

        # If query is vague (like "tell me more", "what about", etc), add minimal context
        if last_user_query and ("more" in query.lower() or "about" in query.lower() or "that" in query.lower()):
            reformed = f"{query} regarding {last_user_query}"
            self.logger.info(f"Reformatted: '{query}' -> '{reformed}'")
            return reformed

        # Default: return as-is
        self.logger.info(f"Returning query as-is: '{query}'")
        return query

    # ALTERNATIVE: If you want to use LLM reformulation, use THIS simpler prompt:
    async def reformalize_conversation_with_llm(self, project_id: int, query: str, history_messages: List) -> str:
        """
        Use LLM for reformulation with a VERY strict, simple prompt.
        No chat history passed to LLM (to avoid contamination).
        """
        if not history_messages:
            return query

        # Create a SIMPLE summary of what was discussed (no full messages)
        context_topics = []
        for msg in history_messages:
            msg_role = msg.get("role", "").lower() if isinstance(msg, dict) else ""
            msg_content = msg.get("content", "").strip() if isinstance(msg, dict) else ""
            
            if msg_role in ["user", "human"] and msg_content:
                # Extract first 50 chars as topic hint
                topic = msg_content[:50]
                context_topics.append(topic)

        context_hint = " | ".join(context_topics[-2:]) if context_topics else ""  # Last 2 queries only

        # CRITICAL: Create prompt WITHOUT chat history to avoid LLM hallucination
        simple_reform_prompt = f"""You are a query reformulation assistant. Your ONLY job is to take a question and make it standalone by adding minimal context.

STRICT RULES:
1. Return ONLY the reformulated query, nothing else
2. Do NOT add preambles like "According to..."
3. Do NOT change the meaning of the question
4. If the question is already standalone, return it EXACTLY as-is
5. Keep it short and simple

Previous conversation topics: {context_hint}
Current question: {query}

Reformulated standalone query (ONLY the query, no explanation):"""

        try:
            reformed = self.generation_client.generate_text(prompt=simple_reform_prompt)
            
            if not reformed or not reformed.strip():
                self.logger.warning(f"Reformulation returned empty. Using original: '{query}'")
                return query

            cleaned = reformed.strip()
            
            # Safety check: if it's way longer than original or contains answer preambles, reject it
            if len(cleaned) > len(query) * 2:
                self.logger.warning(f"Reformulation too long ({len(cleaned)} chars). Using original: '{query}'")
                return query
            
            if any(phrase in cleaned.lower() for phrase in ["according to", "based on", "the provided", "here is", "here's"]):
                self.logger.warning(f"Reformulation contains preamble. Using original: '{query}'")
                return query
            
            # Check if it's the same as any history message (guardrail)
            for msg in history_messages:
                msg_role = msg.get("role", "").lower() if isinstance(msg, dict) else ""
                if msg_role in ["assistant", "bot", "chatbot"]:
                    msg_content = msg.get("content", "").strip() if isinstance(msg, dict) else ""
                    if msg_content and msg_content[:100].lower() in cleaned.lower():
                        self.logger.warning(f"Reformulation matches assistant response. Using original: '{query}'")
                        return query
            
            self.logger.info(f"Reformatted: '{query}' -> '{cleaned}'")
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error reformulating: {str(e)}")
            return query

    async def history_aware_retriever(self, project_id: int, query: str, history_messages: List, limit: int = 5):
        self.logger.info(f"history_aware_retriever called with {len(history_messages)} history messages for query: '{query}'")

        reformatted_query = await self.reformalize_conversation(
            project_id=project_id,
            query=query,
            history_messages=history_messages
        )

        self.logger.info(f"Final Query used for embedding & search: '{reformatted_query}'")

        vectors = self.embedding_client.embed_text(
            text=reformatted_query,
            document_type=DocumentTypeEnum.QUERY
        )
        
        if not vectors:
            return reformatted_query, []

        query_embedding = vectors[0] if isinstance(vectors, list) and len(vectors) > 0 else None
        
        if not query_embedding:
            return reformatted_query, []

        collection_name = self.create_table_name(project_id)

        docs_results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=query_embedding,
            limit=limit 
        )

        return reformatted_query, docs_results or []

    async def index_conversation_into_DB(self, project_id: int, conversation_messages: List):
        collection_name = self.create_table_name(project_id=project_id)

        texts = [c.chunk_text for c in conversation_messages]
        metadata = [c.chunk_metadata for c in conversation_messages]

        vectors = self.embedding_client.embed_text(
            text=texts,
            document_type=DocumentTypeEnum.DOCUMENT
        )

        await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size
        )

        await self.vectordb_client.insert_many_collections(
            collection_name=collection_name,
            texts=texts,
            embeddings=vectors,
            metadata=metadata,
            batch_size=50,
            record_ids=list(range(len(conversation_messages)))
        )

        return True

    async def search_vector_db_collection(self, project: Project, text: str, limit: int) -> list:
        collection_name = self.create_table_name(project_id=project.project_id)
        vectors = self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnum.QUERY)
        
        if not vectors:
            return []

        query_vector = vectors[0] if isinstance(vectors, list) and len(vectors) > 0 else None
        
        if not query_vector:
            return []

        search_results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=query_vector,
            limit=limit
        )

        return search_results or []

    async def answer_rag_question(self, project: Project, conversation: Optional[Conversation], query: str, limit: int = 5):
        # 1. Retrieve context documents based on whether conversation history exists
        if conversation and conversation.content and len(conversation.content) > 0:
            self.logger.info(f"Using history-aware retriever. History size: {len(conversation.content)}")
            reformatted_query, docs_results = await self.history_aware_retriever(
                project_id=project.project_id,
                query=query,
                history_messages=conversation.content,
                limit=limit
            )
        else:
            self.logger.info(f"No history or empty history. Using direct retrieval.")
            reformatted_query = query
            docs_results = await self.search_vector_db_collection(project=project, text=query, limit=limit)

        docs_results = docs_results or []
    
        # 2. Return early if no relevant documents are retrieved
        if not docs_results:
            footer_prompt = self.template_parser.get("rag", "footer_prompt")
            full_prompt = "\n\n".join([f"User question: {reformatted_query}", footer_prompt])
        
            # LLM will return "information not available" message
            system_prompt = self.template_parser.get("rag", "system_prompt")
            chat_history = [
                self.generation_client.construct_prompt(
                    prompt=system_prompt, 
                    role=self.generation_client.enums.SYSTEM.value
                )
            ]
            
            answer = self.generation_client.generate_text(
                prompt=full_prompt,
                chat_history=chat_history
            )
            
            return answer, full_prompt, {
                "conversation_history": conversation.content if conversation else [],
                "retrieved_documents": []
            }

        # 3. Construct system, document, and footer prompts
        system_prompt = self.template_parser.get("rag", "system_prompt")
        
        document_prompts = "\n\n".join([
            self.template_parser.get("rag", "document_prompt", {
                "doc_num": idx + 1,
                "chunk_text": self.generation_client.process_text(doc.text)
            }) for idx, doc in enumerate(docs_results)
        ])
        footer_prompt = self.template_parser.get("rag", "footer_prompt")

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt, 
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        # Add conversation history to chat context
        if conversation and conversation.content:
            for msg in conversation.content:
                role_val = self.generation_client.enums.USER.value if msg.get("role") in ["user", "human"] else self.generation_client.enums.ASSISTANT.value
                chat_history.append(
                    self.generation_client.construct_prompt(
                        prompt=msg.get("content", ""),
                        role=role_val
                    )
                )

        # Build full_prompt with original query
        full_prompt = "\n\n".join([
            f"Context:\n{document_prompts}",
            f"User question: {query}",
            footer_prompt
        ])

        # 4. Generate the response text from the LLM
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        # 5. Prepare user query and assistant answer entries
        new_messages = [
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer}
        ]

        # 6. Apply state persistence logic: UPDATE existing vs. CREATE new
        if conversation:
            current_content = list(conversation.content) if conversation.content else []
            current_content.extend(new_messages)
            conversation.content = current_content
            updated_conv = await self.db_client.update_conversation(conversation=conversation)
            # Use the returned updated conversation object
            if updated_conv:
                conversation = updated_conv
                self.logger.info(f"Updated conversation with {len(current_content)} messages")
            else:
                self.logger.warning(f"Update returned None, using local conversation object")
        else:
            conversation_title = query[:50].strip() if query else "New Conversation"
            new_conversation_obj = Conversation(
                conversation_project_id=project.project_id,
                title=conversation_title,
                content=new_messages
            )
            conversation = await self.db_client.create_conversation(
                project_id=project.project_id, 
                conversation=new_conversation_obj
            )
            self.logger.info(f"Created new conversation with ID: {conversation.conversation_id if conversation else 'Unknown'}")
        
        # 7. Convert Pydantic/dataclass document objects to dictionaries
        formatted_docs = [
            doc.dict() if hasattr(doc, 'dict') else doc.__dict__ 
            for doc in docs_results
        ]

        return answer, full_prompt, {
            "conversation_history": conversation.content if conversation else new_messages,
            "retrieved_documents": formatted_docs
        }

    async def summarize_conversation(self, project_id: int, conversation: Conversation) -> str:
        if not conversation.content:
            return "No conversation history available to summarize."
    
        formatted_history = []
        for message in conversation.content:
            if isinstance(message, dict):
                text_content = message.get("message") or message.get("content") or message.get("text")
                raw_role = str(message.get("role", "user")).lower()
                
                if raw_role in ["assistant", "bot", "chatbot"]:
                    role = "Chatbot"
                elif raw_role == "system":
                    role = "System"
                elif raw_role == "tool":
                    role = "Tool"
                else:
                    role = "User"
            
                if text_content and str(text_content).strip():
                    formatted_history.append({
                        "role": role,
                        "message": str(text_content).strip()
                    })
            elif isinstance(message, str) and message.strip():
                formatted_history.append({
                    "role": "User",
                    "message": message.strip()
                })

        if not formatted_history:
            return "No valid conversation content to summarize."

        # Convert the dictionary list to a clear text representation for the Prompt
        conversation_text_for_prompt = "\n".join([f"{msg['role']}: {msg['message']}" for msg in formatted_history])

        # Inject the conversation directly into the Template variable '$conversation'
        summary_prompt = self.template_parser.get("rag", "summary_ticket_prompt", {
            "conversation": conversation_text_for_prompt
        })
    
        # Generate the summary text
        summary = self.generation_client.generate_text(
            prompt=summary_prompt
        )
        
        conversation.summary_ticket = summary
        await self.db_client.update_conversation(conversation=conversation)
        return summary

    async def email_ticket_to_customer_service(self, project_id: int, conversation: Conversation, recipient_email: str) -> bool:
        if not conversation.summary_ticket:
            summary = await self.summarize_conversation(project_id=project_id, conversation=conversation)
        else:
            summary = conversation.summary_ticket

        subject = f"[Support Ticket #{conversation.conversation_id}] Project {project_id}"
    
        body = f"""==================================================
NEW SUPPORT TICKET
==================================================

[ METADATA ]
• Project ID      : {project_id}
• Conversation ID : {conversation.conversation_id}
• Session UUID    : {conversation.conversation_uuid}

[ SUMMARY & ACTION ITEMS ]
{summary}

--------------------------------------------------
Automated summary generated from user conversation.
=================================================="""

        msg = MIMEMultipart()
        msg['From'] = self.app_settings.SMTP_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        def send_smtp_email():
            server_host = self.app_settings.SMTP_SERVER
            server_port = self.app_settings.SMTP_PORT

            if not server_host or not self.app_settings.SMTP_USERNAME:
                raise ValueError("SMTP server configurations are missing in settings.")

            if server_port == 465:
                with smtplib.SMTP_SSL(server_host, server_port, timeout=10) as server:
                    if self.app_settings.SMTP_USERNAME and self.app_settings.SMTP_PASSWORD:
                        server.login(self.app_settings.SMTP_USERNAME, self.app_settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(server_host, server_port, timeout=10) as server:
                    if getattr(self.app_settings, 'SMTP_USE_TLS', True):
                        server.starttls()
                    if self.app_settings.SMTP_USERNAME and self.app_settings.SMTP_PASSWORD:
                        server.login(self.app_settings.SMTP_USERNAME, self.app_settings.SMTP_PASSWORD)
                    server.send_message(msg)

        try:
            await asyncio.to_thread(send_smtp_email)
            self.logger.info(f"Successfully emailed ticket for conversation {conversation.conversation_id} to {recipient_email}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send ticket email: {str(e)}")
            return False