"""
Data upload and processing routes for the SmartDesk application.

This module defines the endpoints responsible for receiving file uploads
(like PDFs), validating them, saving them to the filesystem and database,
and triggering the document chunking process for the RAG pipeline.
"""
from fastapi import APIRouter, Depends, File, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
import logging
import aiofiles
from src.helpers.config import get_settings, Settings
from src.controllers import DataController, ProjectController, ProcessController
from src.models.enums.ResponseSignal import ResponseSignal
from src.schemas.data import ProcessRequest
from src.models.ProjectModel import ProjectModel
from src.models.ChunkModel import ChunkModel
from src.models.AssetModel import AssetModel
from src.models.db_schemas import DataChunk, Asset
from src.models.enums.AssetTypeEnum import AssetTypeEnum
from src.controllers import NLPController
logger = logging.getLogger('uvicorn.error')

app_settings = Settings()

data_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, file: UploadFile = File(...)):
    """
    Handles the streaming upload of a file for a specific project.

    This endpoint validates the file, generates a unique storage path,
    streams the file to disk to prevent memory overload, and records
    the asset in the MongoDB database.

    Args:
        request (Request): The FastAPI request object (used to access the DB client).
        project_id (str): The unique identifier of the target project.
        file (UploadFile): The uploaded file object.

    Returns:
        JSONResponse: A response indicating success or failure, including the new file ID on success.
    """
    # Ensure the project exists in the database
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    # Validate the file properties (size, extension)
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

    # Prepare the filesystem paths
    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    # Save the file asynchronously in chunks
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    # Store the asset record in the database
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_resource = Asset(
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.asset_id),
        }
    )

@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: int, process_request: ProcessRequest):
    """
    Triggers the text extraction and chunking process for a project's files.

    This endpoint reads files from disk, splits them into semantic chunks using
    LangChain, and bulk inserts the resulting chunks into MongoDB for later retrieval.
    It supports processing a single file or all files in a project, and can optionally
    reset (delete) existing chunks before processing.

    Args:
        request (Request): The FastAPI request object.
        project_id (str): The unique identifier of the target project.
        process_request (ProcessRequest): The request payload containing chunking parameters.

    Returns:
        JSONResponse: A response detailing the success of the operation, including
            the number of processed files and inserted chunks.
    """
    chunk_size = process_request.chunk_size
    overlap_size = process_request.chunk_overlap
    do_reset = process_request.do_reset

    # Retrieve project context
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    nlp_controller = NLPController(vectordb_client=request.app.vectordb_client,
                                   generation_client=request.app.generation_client,
                                   embedding_client=request.app.embedding_client,
                                   template_parser=request.app.template_parser)

    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    # Determine which files need to be processed
    project_files_ids = {}
    if process_request.file_id:
        # Process a single specific file
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.project_id,
            asset_id=int(process_request.file_id)
        )

        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                }
            )

        project_files_ids = {
            asset_record.asset_id: asset_record.asset_name
        }
    
    else:
        # Process all files in the project
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
        )

        project_files_ids = {
            record.asset_id: record.asset_name
            for record in project_files
        }

    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
            }
        )
    
    process_controller = ProcessController(project_id=project_id)

    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    # Optionally clear old chunks before generating new ones
    if do_reset == 1:
        collection_name=nlp_controller.create_collection_name(project_id=project.project_id)
        
        #delete assicoated vector collection
        _=await request.app.vectordb_client.delete_collection(collection_name=collection_name)

        
        #delete all chunks from db 
        _=await chunk_model.delete_chunks_by_project_id(
            project_id=project.project_id

        )

        

        


    # Process each selected file
    for asset_id, file_id in project_files_ids.items():

        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue

        # Split the loaded document into smaller chunks
        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESSING_FAILED.value
                }
            )

        # Map LangChain Document objects to our database schema
        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.project_id,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        # Bulk insert the new chunks
        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )
