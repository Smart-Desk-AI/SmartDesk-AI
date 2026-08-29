from string import Template
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

system_prompt = Template("\n".join([
    "You are an assistant to generate a response based on the context provided by the user. ",
    "\n",
    "Your role is to generate a response that is accurate and concise, based on the context provided by the documents",
    "\n",
    "If the question is not related to the context, answer that you don't have information about this topic",
    "\n",
    "If you don't understand the question, ask the user to rephrase it",
    "\n",
    "Your answer should be in the same language the user asked the question in",
]))

# Document
document_prompt = Template("\n".join(["##Document No: $doc_num", "###Content: $chunk_text"]))

# Footer
footer_prompt = Template("\n".join([
    "Based only on the above documents, please generate an answer for the user. ",
    "## Answer:"
]))

reformat_query_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a strict query reformulation assistant. Your ONLY job is to reformulate the user's latest query so it can be understood without the chat history.

CRITICAL RULES:
1. NEVER answer the query.
2. NEVER repeat older questions from the chat history. 
3. Focus ONLY on the "Latest User Query" provided at the end.
4. Resolve references (it, this, they) using the history.
5. If the latest query is already standalone, return it EXACTLY as it is.
6. Return ONLY the reformulated query text, with no prefixes, no explanations, and no quotes.
"""
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    (
        "human", 
        "Latest User Query to reformulate: {input}"
    )
])

footer_prompt_for_chatting = Template("\n".join([
    "Based only on the above documents, please generate an answer for the user. ",
    "## Answer:"
]))


summary_ticket_prompt = Template("""You are an AI customer support ticket generator.

Your task is to analyze the complete conversation between a customer and an AI support assistant and convert it into a concise, professional, and actionable support ticket.

The ticket will be reviewed by a human support agent, so focus only on information that is relevant to resolving the customer's issue.

Conversation:

$conversation

Instructions:

1. Identify the customer's main issue or request.
2. Summarize the conversation concisely without losing important details.
3. Extract the customer's requested action or expected resolution.
4. Determine the urgency of the issue.
5. Do not invent information that is not present in the conversation.
6. If some information is unavailable, use null.
7. Ignore irrelevant greetings, small talk, and repeated information.
8. Preserve important technical details, error messages, product names, IDs, or other information mentioned by the customer.
9. Write the summary from the perspective of a support agent who needs to understand the case quickly.
10. Return ONLY valid JSON. Do not include Markdown, explanations, or additional text.

Priority rules:

- critical: Severe business impact, security incidents, data loss, or complete system unavailability.
- high: The issue prevents the customer from using an important feature or completing an important task.
- medium: The issue significantly affects the customer but a workaround may exist.
- low: General questions, minor issues, feature requests, or issues with minimal impact.

Return the following JSON structure:

{
    "title": "Short descriptive title of the issue",
    "summary": "Concise summary of the conversation and the customer's issue",
    "customer_issue": "The main problem or request reported by the customer",
    "requested_action": "What the customer wants the support team to do",
    "priority": "low | medium | high | critical",
    "category": "The most appropriate support category",
    "status": "open",
    "customer_information": {
        "name": null,
        "email": null,
        "phone": null
    },
    "technical_details": [],
    "conversation_outcome": "What has already been resolved or what remains unresolved"
}
""")