import logging
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


@conversation_router.post("/chat/{project_id}")
async def chat(request: Request, project_id: int, search_request: SearchRequest):
    # 1. Fetch or create project instance
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )

    # 2. Fetch existing conversation history for this project
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )
    conversation = await conversation_model.get_conversation(
        project_id=project_id
    )

    # 3. Instantiate NLP Controller (Passing conversation_model as db_client)
    conversation_instance = ConversationNLPController(
        db_client=conversation_model,
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    # 4. Process RAG Question & update/create conversation in DB
    answer, full_prompt, rag_context = await conversation_instance.answer_rag_question(
        project=project,
        conversation=conversation,
        query=search_request.text,
        limit=search_request.limit
    )

    # 5. Formulate API response
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
    conversation_model = await ConversationModel.create_instance(
        db_client=request.app.db_client
    )
    conversation = await conversation_model.close_conversation(
        project_id=project_id
    )
    if conversation:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": ResponseSignal.CONVERSATION_CLOSED.value,
                "conversation": conversation
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.CONVERSATION_NOT_FOUND.value,
                "conversation": None
            }
        )