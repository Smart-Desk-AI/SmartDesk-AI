import logging
from pydantic import BaseModel
from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from src.helpers.config import Settings
from src.controllers.ConversationNLPController import ConversationNLPController
from src.models.enums.ResponseSignal import ResponseSignal
from src.models.ProjectModel import ProjectModel
from src.models.ConversationModel import ConversationModel
from src.schemas.nlp import SearchRequest

logger = logging.getLogger('uvicorn.error')
app_settings = Settings()

conversation_router = APIRouter(
    prefix="/api/v1/conversation",
    tags=["api_v1", "conversation"],
)

# Pydantic schema for the email request body
class EmailTicketRequest(BaseModel):
    recipient_email: str
    smtp_config: dict


@conversation_router.post("/chat/{project_id}")
async def chat(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value}
        )

    conversation_model = await ConversationModel.create_instance(db_client=request.app.db_client)
    conversation = await conversation_model.get_conversation(project_id=project_id)

    conversation_instance = ConversationNLPController(
        db_client=conversation_model,
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    answer, full_prompt, rag_context = await conversation_instance.answer_rag_question(
        project=project,
        conversation=conversation,
        query=search_request.text,
        limit=search_request.limit
    )

    if answer:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
                "answer": answer,
                "full_prompt": full_prompt,
                "conversation_history": rag_context.get("conversation_history", []),
                "retrieved_documents": rag_context.get("retrieved_documents", [])
            }
        )

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "signal": ResponseSignal.RAG_ANSWER_FAILED.value,
            "answer": None
        }
    )


@conversation_router.post("/chat/{project_id}/close")
async def close_conversation(request: Request, project_id: int):
    conversation_model = await ConversationModel.create_instance(db_client=request.app.db_client)
    conversation = await conversation_model.close_conversation(project_id=project_id)
    
    if conversation:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.CONVERSATION_CLOSED.value,
                "conversation_id": conversation.conversation_id  # Serialized attribute instead of ORM object
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.CONVERSATION_NOT_FOUND.value,
                "conversation_id": None
            }
        )


@conversation_router.post("/chat/{project_id}/summarized_ticket_email")
async def send_summarized_ticket_email(request: Request, project_id: int, payload: EmailTicketRequest):
    conversation_model = await ConversationModel.create_instance(db_client=request.app.db_client)
    conversation = await conversation_model.get_conversation(project_id=project_id)
    
    if not conversation:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.CONVERSATION_NOT_FOUND.value,
                "conversation_id": None
            }
        )

    conversation_instance = ConversationNLPController(
        db_client=conversation_model,
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )
    
    # Send email (the method automatically handles summarization if it hasn't been done yet)
    # Passing payload.smtp_config safely if provided, otherwise the controller falls back to .env
    email_sent = await conversation_instance.email_ticket_to_customer_service(
    project_id=project_id,
    conversation=conversation,
    recipient_email=payload.recipient_email)

    if email_sent:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.SUMMARIZED_AND_EMAILED_SUCCESS.value,
                "conversation_id": conversation.conversation_id
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.SUMMARIZED_AND_EMAILED_FAILED.value,
                "conversation_id": conversation.conversation_id
            }
        )