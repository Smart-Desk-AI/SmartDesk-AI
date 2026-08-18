"""
Database interaction model for managing document chunks.

This module provides the `ChunkModel` class, which handles all database operations
related to storing and retrieving text chunks generated during document processing.
These chunks are typically used in Retrieval-Augmented Generation (RAG) pipelines.
"""
from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk    
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne
from sqlalchemy.future import select
from sqlalchemy import delete,func

class ChunkModel(BaseDataModel):
    """
    Model for interacting with the chunks collection in MongoDB.

    Inherits from `BaseDataModel`. Manages the insertion (both single and bulk)
    and deletion of text chunk documents, ensuring that chunks are properly 
    linked to their respective projects.
    """

    def __init__(self, db_client: object):
        """
        Initializes the ChunkModel and binds it to the chunks collection.

        Args:
            db_client (object): The active MongoDB database instance.
        """
        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        """
        Asynchronous factory method to create an initialized ChunkModel instance.

        Args:
            db_client (object): The active MongoDB database instance.

        Returns:
            ChunkModel: A fully initialized instance with the collection and indexes prepared.
        """
        instance = cls(db_client)
        return instance 

    async def create_chunk(self, chunk: DataChunk):
        """
        Inserts a single chunk document into the database.

        Args:
            chunk (DataChunk): The validated chunk model to insert.

        Returns:
            DataChunk: The chunk model updated with the database's inserted _id.
        """
        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)

            return chunk

    async def get_chunk(self, chunk_id: str = None):
        """
        Retrieves a specific chunk by its MongoDB ObjectId.

        Args:
            chunk_id (str, optional): The string representation of the chunk's ObjectId.

        Returns:
            DataChunk | None: The populated chunk model if found, otherwise None.
        """
        async with self.db_client() as session:
            async with session.begin():
                query=select(DataChunk).where(DataChunk.chunk_id==chunk_id)
                chunk=query.scalar_one_or_none()
                if chunk is None:
                    return None
                else:
                    return chunk 

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        """
        Inserts multiple chunk documents efficiently using MongoDB bulk write operations.

        This is crucial for performance when processing large documents that produce
        hundreds or thousands of chunks.

        Args:
            chunks (list): A list of DataChunk Pydantic models.
            batch_size (int, optional): The number of chunks to insert per bulk operation.
                Defaults to 100 to balance memory usage and network round trips.

        Returns:
            int: The total number of chunks processed.
        """
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    # Slice the chunks list into manageable batches
                    batch = chunks[i:i + batch_size]
            
                # Prepare and execute the bulk write operation for the current batch
                    session.add_all(batch)
                await session.commit()

            return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        """
        Deletes all chunks associated with a specific project.

        This is used when re-processing a document to clear out stale chunks
        before inserting the newly generated ones, preventing duplicate key errors.

        Args:
            project_id (ObjectId): The MongoDB ObjectId of the project.

        Returns:
            int: The number of chunk documents deleted.
        """
        async with self.db_client() as session:
            async with session.begin():
                query=delete(DataChunk).where(DataChunk.chunk_project_id==project_id)
                results=await session.execute(query)
                await session.commit()
            return results.rowcount


    async def get_project_chunks(self,project_id:ObjectId,page_number:int=1,page_size:int=50):
        async with self.db_client() as session:
            async with session.begin():
                skip_size=page_size*(page_number-1)
                query=select(DataChunk).where(DataChunk.chunk_project_id==project_id).offset(skip_size).limit(page_size)
                result=(await session.execute(query)).scalars().all() 
                return result

    
    async def get_total_chunks_count(self,project_id:ObjectId):
        records_count=0
        async with self.db_client() as session:
            async with session.begin():
                query=select(func.count(DataChunk.id)).where(DataChunk.chunk_project_id==project_id)
                records_count=(await session.execute(query)).scalar() 
        return records_count




