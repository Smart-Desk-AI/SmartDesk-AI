"""
Pydantic schemas for data-related API requests.

This module defines the expected payload structures for incoming HTTP requests
to the data processing endpoints.
"""
from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    """
    Schema for the document processing request payload.

    Defines the parameters required to trigger the text extraction and chunking
    process for files within a project.

    Attributes:
        file_id (str | None): Optional specific file ID to process. If None,
            all files in the project will be processed.
        chunk_size (int): The maximum character length of each extracted text chunk.
        chunk_overlap (int): The number of overlapping characters between adjacent chunks
            to preserve context.
        do_reset (int): A flag (0 or 1) indicating whether to delete existing chunks
            for the project/file before generating new ones. Defaults to 0 (no reset).
    """
    file_id: str = None
    chunk_size: int
    chunk_overlap: int   
    do_reset: Optional[int] = 0
