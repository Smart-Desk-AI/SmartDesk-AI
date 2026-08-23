from pydantic import BaseModel, Field
from typing import List, Optional

class ConversationMessage(BaseModel):
    role: str = Field(..., description="The role of the sender (e.g., 'user', 'assistant', 'system')")
    content: str = Field(..., description="The text content of the message")  # Renamed from 'message' to 'content'


class ConversationQuery(BaseModel):
    project_id: int = Field(..., description="The ID of the project being queried")
    query: str = Field(..., description="The user's current input question")
    history_messages: List[ConversationMessage] = Field(
        default=[], 
        description="Optional prior chat history"
    )


class RetrievedDocumentSchema(BaseModel):
    score: float = Field(..., description="Cosine similarity score")
    text: str = Field(..., description="Retrieved chunk text content")


class ConversationResponse(BaseModel):
    answer: Optional[str] = Field(None, description="The generated LLM answer")
    full_prompt: Optional[str] = Field(None, description="The final prompt sent to the LLM")
    conversation_history: List[ConversationMessage] = Field(default=[])
    retrieved_documents: List[RetrievedDocumentSchema] = Field(default=[])