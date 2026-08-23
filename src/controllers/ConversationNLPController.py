from src.models import ConversationModel
from src.models import ConversationModel
from src.models import ConversationModel
import json
from typing import List, Optional
from src.controllers.BaseController import BaseController 
from src.stores.llm.LLMEnums import DocumentTypeEnum
from src.stores.llm.templates.locales.en.rag import reformat_query_prompt
from src.models.db_schemas import Project, DataChunk, Conversation
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio
from typing import Optional



class ConversationNLPController(BaseController):
    def __init__(self, db_client,generation_client, template_parser, vectordb_client, embedding_client):
        super().__init__()
        self.db_client=db_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.vectordb_client = vectordb_client
        self.logger = logging.getLogger('uvicorn.error')

    def create_table_name(self, project_id: str) -> str:
        return f"collection_384_{project_id}".strip().lower()
    
    async def reformalize_conversation(self, project_id: int, query: str, history_messages: List):
        reformatted_chat_history = reformat_query_prompt.invoke(
            {
                "chat_history": history_messages,
                "input": query
            }
        )

        reformalized_query = self.generation_client.generate_text(
            prompt=reformatted_chat_history.to_string()
        )

        return reformalized_query

    async def history_aware_retriever(self, project_id: int, query: str, history_messages: List, limit: int = 5):
        reformatted_query = await self.reformalize_conversation(
            project_id=project_id,
            query=query,
            history_messages=history_messages
        )

        query_embedding = self.embedding_client.embed_text(
            text=reformatted_query,
            document_type=DocumentTypeEnum.QUERY
        )[0]

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
        if conversation and conversation.content:
            reformatted_query, docs_results = await self.history_aware_retriever(
                project_id=project.project_id,
                query=query,
                history_messages=conversation.content,
                limit=limit
            )
        else:
            reformatted_query = query
            docs_results = await self.search_vector_db_collection(project=project, text=query, limit=limit)

        docs_results = docs_results or []
    
        # 2. Return early if no relevant documents are retrieved
        if not docs_results:
            system_prompt = self.template_parser.get("rag", "system_prompt")
            footer_prompt = self.template_parser.get("rag", "footer_prompt")
            full_prompt = "\n\n".join([reformatted_query, footer_prompt])
        
            return None, full_prompt, {
                "conversation_history": conversation.content if conversation else [],
                "retrieved_documents": []
            }

        # 3. Construct system, document, and footer prompts
        system_prompt = self.template_parser.get("rag", "system_prompt")
        document_prompts = "\n".join([
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

        full_prompt = "\n\n".join([reformatted_query, document_prompts, footer_prompt])

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
        # Case A: Conversation exists -> Append new messages and update DB
            if not conversation.content:
                conversation.content = []
            
            conversation.content.extend(new_messages)
            await self.db_client.update_conversation(conversation=conversation)
        else:
        # Generate a concise title from the initial user query (e.g., first 50 characters)
            conversation_title = query[:50].strip() if query else "New Conversation"

        # Case B: No conversation exists -> Create a new Conversation ORM instance with title
            new_conversation_obj = Conversation(
                conversation_project_id=project.project_id,
                title=conversation_title,
                content=new_messages)
            await self.db_client.create_conversation(
                project_id=project.project_id, 
                conversation=new_conversation_obj)
        
        # 7. Convert Pydantic/dataclass document objects to dictionaries for clean JSON serialization
        formatted_docs = [
            doc.dict() if hasattr(doc, 'dict') else doc.__dict__ 
            for doc in docs_results
        ]

        return answer, full_prompt, {
        "conversation_history": conversation.content if conversation else new_messages,
        "retrieved_documents": formatted_docs}



    async def summarize_conversation(self,project_id: int, conversation: Conversation):
        if not conversation.content:
            return "No conversation history available to summarize."
        
        summary_prompt = self.template_parser.get("rag", "summary_ticket_prompt")
        summary = self.generation_client.generate_text(
            prompt=summary_prompt,
            chat_history=conversation.content
        )
        conversation.summary_ticket = summary
        await self.db_client.update_conversation(conversation=conversation)
        return summary



    async def email_ticket_to_customer_service(self, project_id: int, conversation: Conversation, 
                                                recipient_email: str,smtp_config: dict) -> bool:
        """
        Summarizes the conversation (if not already summarized) and emails the ticket summary
        to customer support using SMTP.
        """
        # 1. Ensure ticket summary exists
        if not conversation.summary_ticket:
            summary = await self.summarize_conversation(project_id=project_id, conversation=conversation)
        else:
            summary = conversation.summary_ticket

        # 2. Build email payload
        subject = f"[Support Ticket] Conversation Summary #{conversation.conversation_id} (Project {project_id})"
        
        body = (
            f"Customer Support Ticket\n"
            f"-----------------------\n"
            f"Project ID: {project_id}\n"
            f"Conversation ID: {conversation.conversation_id}\n"
            f"UUID: {conversation.conversation_uuid}\n\n"
            f"Summary:\n{summary}\n"
        )

        msg = MIMEMultipart()
        msg['From'] = smtp_config.get("sender_email")
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # 3. Offload synchronous SMTP sending to a thread pool to avoid blocking the event loop
        def send_smtp_email():
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get("use_tls", True):
                    server.starttls()
                if smtp_config.get("username") and smtp_config.get("password"):
                    server.login(smtp_config["username"], smtp_config["password"])
                server.send_message(msg)

        try:
            await asyncio.to_thread(send_smtp_email)
            self.logger.info(f"Successfully emailed ticket for conversation {conversation.conversation_id} to {recipient_email}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send ticket email: {str(e)}")
            return False