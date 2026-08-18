from fastapi import APIRouter, Depends, File, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
import logging
import aiofiles
from src.helpers.config import get_settings, Settings
from src.controllers import DataController, ProjectController, ProcessController
from src.controllers.NLPController import NLPController
from src.models.enums.ResponseSignal import ResponseSignal
from src.schemas.data import ProcessRequest
from src.models.ProjectModel import ProjectModel
from src.models.ChunkModel import ChunkModel
from src.models.AssetModel import AssetModel
from src.models.db_schemas import DataChunk, Asset
from src.models.enums.AssetTypeEnum import AssetTypeEnum
from src.schemas.nlp import PushRequest, SearchRequest
from src.models.db_schemas import RetrivedDocument
from tqdm.auto import tqdm

logger = logging.getLogger('uvicorn.error')

app_settings = Settings()

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):
    """
    Index all chunks of a project to the vector database.
    """

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value}
        )

    nlp_controller_instance = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    inserted_count = 0
    has_records = True
    page_number = 1
    idx = 0


    #creating_collection if not exist
    collection_name=nlp_controller_instance.create_collection_name(project_id=project.project_id)
    _=await request.app.vectordb_client.create_collection(
        collection_name=collection_name,
        embedding_size=request.app.embedding_client.embedding_size,
        do_reset=push_request.do_rest)

    #setup batching
    total_chunks_count=await chunk_model.get_total_chunks_count(project_id=project.project_id)
    pbar=tqdm(total=total_chunks_count,desc="Vector indexing",position=0)

    


    while has_records:
        page_chunks = await chunk_model.get_project_chunks(
            project_id=project.project_id,
            page_number=page_number,
            page_size=push_request.page_size
        )

        if len(page_chunks):
            page_number += 1

        if len(page_chunks) == 0:
            has_records = False
            break

        chunks_ids = [chunk.chunk_id for chunk in page_chunks]
        idx += len(page_chunks)

        is_inserted =await nlp_controller_instance.index_into_vectordb(
            project=project,
            chunks=page_chunks,
            do_rest=push_request.do_rest,
            chunks_ids=chunks_ids
        )

        

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "signal": ResponseSignal.INSERT_INTO_VECTOR_DB_FAILED.value
                }
            )

        pbar.update(len(page_chunks))
        inserted_count += len(page_chunks)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            "inserted_count": inserted_count
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
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

    nlp_controller_instance = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    collection_info = await nlp_controller_instance.get_vector_collection_info(
        project=project
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request,
    project_id: int,
    search_request: SearchRequest
):
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

    nlp_controller_instance = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    results =await nlp_controller_instance.search_vector_db_collection(
        project=project,
        text=search_request.text,
        limit=search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.SEARCH_FAILED.value,
                "results": []
            }
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.SEARCH_SUCCESS.value,
            "search_results": [result.dict() for result in results]
        }
    )


@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(
    request: Request,
    project_id: int,
    search_request: SearchRequest
):
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

    nlp_controller_instance = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    answer, full_prompt, chat_history =await nlp_controller_instance.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "signal": ResponseSignal.RAG_ANSWER_FAILED.value,
                "answer": {}
            }
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )