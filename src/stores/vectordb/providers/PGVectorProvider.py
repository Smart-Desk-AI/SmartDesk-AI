from importlib.resources import path
from typing import List
from src.stores.vectordb.VectorDBInterface import VectorDBInterface
import logging
from src.stores.vectordb.VectorDBEnums import PgVectorVectorIndexMethodEnum,PgVectorDistanceMethodEnum,PgVectorTableschemaEnums
from src.models.db_schemas import RetrivedDocument  
from sqlalchemy.sql import text as sql_text
from sqlalchemy import bindparam
import json
from sqlalchemy.dialects.postgresql import JSONB


class PGVectorProvider(VectorDBInterface):
    def __init__(self,db_client=None,default_vector_size:int=786,distance_method:str=None,index_threshold:int=100):
    
        self.logger = logging.getLogger("uvicorn")
        self.db_client=db_client
        self.default_vector_size=default_vector_size
        self.distance_method=distance_method

        self.pgvector_table_prefix=PgVectorTableschemaEnums._PREFIX.value

        if distance_method==PgVectorDistanceMethodEnum.COSINE.value:
            self.distance_method=PgVectorDistanceMethodEnum.COSINE.value
        elif distance_method==PgVectorDistanceMethodEnum.DOT_PRODUCT.value:
            self.distance_method=PgVectorDistanceMethodEnum.DOT_PRODUCT.value    
        else:
            self.logger.error("Invalid distance method")
            self.distance_method=PgVectorDistanceMethodEnum.COSINE.value


        self.logger.info("PGVectorProvider initialized")
        self.logger.info(f"DB Path: {self.db_client}")
        self.logger.info(f"Distance Method: {self.distance_method}")




    async def get_pgvector_index_name(self,collection_name:str)-> str :
        return f"{collection_name}_vector_idx"



    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(f"CREATE EXTENSION IF NOT EXISTS vector;"))
                self.logger.info("Extension 'vector' enabled successfully")
                self.logger.info("PGVectorProvider connected")
            await session.commit()
            return True    



    async def dis_connect(self):
        pass



    async def is_collection_exists(self,collection_name:str)-> bool :
        record=None
        async with self.db_client() as session:
            async with session.begin():
                list_tbl=sql_text(f"SELECT * FROM pg_tables WHERE tablename= :collection_name")
                result=await session.execute(list_tbl,{"collection_name":collection_name})
                record=result.scalar_one_or_none()

        return record      



    async def list_all_collections(self)->list:
        records=[]
        async with self.db_client() as session:
            async with session.begin():

                list_tbl= sql_text(f"select table_name from pg_tables where tablename like :prefix")

                results = await session.execute(list_tbl,{"prefix": f"{self.pgvector_table_prefix}%"})
                records=results.scalars().all()

        return records



    async def get_collection_info(self,collection_name:str)-> dict:
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql=sql_text(f"SELECT schemaname,tablename,tableowner,tablespace,hasindexes FROM pg_tables WHERE tablename='{collection_name}'")
                count_sql=sql_text(f"SELECT count(*) FROM {collection_name}")
                
                table_info=await session.execute(table_info_sql)
                record_count=await session.execute(count_sql)


                table_data=table_info.fetchone()
                if not table_data:
                    return None

                return{
                    "table_info": dict(table_data._mapping),
                    "record_count":record_count
                }



    async def delete_collection(self,collection_name:str)->bool:
        async with self.db_client() as session:
            async with session.begin():
                self.logger.info(f"Deleting collection {collection_name}")
                await session.execute(sql_text(f"DROP TABLE IF EXISTS {collection_name}"))
                await session.commit()
                self.logger.info(f"Collection {collection_name} deleted successfully")
        return True



    async def create_collection(self,collection_name:str,
                                     embedding_size:int,
                                     do_reset:bool=False)->bool:


            if do_reset:
                await self.delete_collection(collection_name=collection_name)

            is_collection_exists= await self.is_collection_exists(collection_name=collection_name)

            if is_collection_exists:
                self.logger.info(f"Collection {collection_name} already exists")
                return False
            
            async with self.db_client() as session:
                async with session.begin():
                    create_sql=sql_text(f"""
                        CREATE TABLE {collection_name}(
                        {PgVectorTableschemaEnums.ID.value} BIGSERIAL PRIMARY KEY,
                        {PgVectorTableschemaEnums.TEXT.value} text,
                        {PgVectorTableschemaEnums.METADATA.value} jsonb DEFAULT \'{{}}\',
                        {PgVectorTableschemaEnums.VECTOR.value} vector({embedding_size}),
                        {PgVectorTableschemaEnums.CHUNK_ID.value} integer,
                        FOREIGN KEY ({PgVectorTableschemaEnums.CHUNK_ID.value}) REFERENCES datachunks(chunk_id)
                    )""")

                    await session.execute(create_sql)
                    await session.commit() 
            return True



    async def is_index_existed(self,collection_name:str)->bool:
        index_name=await self.get_pgvector_index_name(collection_name=collection_name)
        async with self.db_client() as session:
            async with session.begin():
                check_sql = sql_text(f"""
                    SELECT *
                    FROM pg_indexes
                    WHERE tablename = '{collection_name}'
                    AND indexname = '{index_name}'
                """)
                results=await session.execute(check_sql)
                records=results.scalar_one_or_none()
                

        return bool(records)   



    async def create_vector_index(self,collection_name:str,index_type:str=PgVectorVectorIndexMethodEnum.HNSW.value,index_threshold :int=100):

        is_index_existed= await self.is_index_existed(collection_name=collection_name)

        if is_index_existed:
            self.logger.info(f"Index {collection_name} already exists")
            return False

        async with self.db_client() as session:
            async with session.begin():
                count_query=sql_text(f"""
                SELECT COUNT(*) FROM {collection_name}
                """)
                record_count=await session.execute(count_query)
                record_count=record_count.scalar_one()
                if record_count>index_threshold:
                    self.logger.info("Creating HNSW index")
                    index_name=await self.get_pgvector_index_name(collection_name=collection_name)
                    create_index_sql=f"""
                    CREATE INDEX {index_name} ON {collection_name} USING HNSW ({PgVectorTableschemaEnums.VECTOR.value} {self.distance_method})
                    """
                    await session.execute(sql_text(create_index_sql))
                    await session.commit()
                    self.logger.info(f"HNSW index {collection_name} created successfully")
                    return True

                else:
                    self.logger.info(f"Record count is less than index threshold : {index_threshold} skipping HNSW index creation")
                    return False
                    



    async def reset_vector_index(self,collection_name:str,index_type:str=PgVectorVectorIndexMethodEnum.HNSW.value):
         
        index_name=await self.get_pgvector_index_name(collection_name=collection_name)

        
        async with self.db_client() as session:
            async with session.begin():
                delete_index_sql=sql_text(f"DROP INDEX IF EXISTS {index_name}")
                await session.execute(delete_index_sql)
                await session.commit()
                self.logger.info(f"Index {index_name} deleted successfully")
                return True

        return self.create_vector_index(collection_name=collection_name,index_type=index_type)



        


    async def insert_one_collection(self,collection_name:str,
                                         embedding:List[float],
                                         metadata:dict=None,
                                         record_id:str=None,
                                         text:str=None):


        is_collection_existed=await self.is_collection_exists(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist")
            return False
            
            
        if not record_id:
            self.logger.error(f"Record ID is required")
            return False
            
            
        async with self.db_client() as session:
            async with session.begin():
                insert_sql=sql_text(f"""
                INSERT INTO {collection_name}(
                    {PgVectorTableschemaEnums.TEXT.value},
                    {PgVectorTableschemaEnums.METADATA.value},
                    {PgVectorTableschemaEnums.VECTOR.value},
                    {PgVectorTableschemaEnums.CHUNK_ID.value}
                    )
                    VALUES(
                        :text,
                        :metadata,
                        :vector,
                        :chunk_id
                    )
                """)

                await session.execute(insert_sql,
                {
                    "text":text,
                    "metadata":metadata,
                    "vector":"["+ ",".join([str(vector_dim) for vector_dim in embedding]) + "]",
                    "chunk_id":record_id
                }).bindparams(bindparam("metadata", type_=JSONB))
                
                await session.commit()
        await self.create_vector_index(collection_name=collection_name)

        return True






    async def insert_many_collections(self,collection_name:str,
                                        texts:List[str]=None,
                                        embeddings:List[List[float]]=None,
                                        metadata:List[dict]=None,
                                        record_ids:List[str]=None,
                                        batch_size:int=50):


        is_collection_existed=await self.is_collection_exists(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist")
            return False
        
        if len(embeddings)!= len(record_ids):
            self.logger.error(f"Record IDs and Embeddings must be equal")
            return False



        if len(metadata)==0 or not metadata:
            metadata=[None]*len(texts) 


        
            
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0,len(texts),batch_size):
                    batch_text=texts[i:i+batch_size]
                    batch_vectors=embeddings[i:i+batch_size]
                    batch_metadata=metadata[i:i+batch_size]
                    batch_record_ids=record_ids[i:i+batch_size]



                    values=[]

                    for _text,_vector,_metadata,_record_id in zip(batch_text,batch_vectors,batch_metadata,batch_record_ids):

                        values.append(
                            {
                                "text":_text,
                                "metadata":_metadata,
                                "vector":"["+ ",".join([str(vector_dim) for vector_dim in _vector]) + "]",
                                "chunk_id":_record_id
                            }
                        )



                    batch_insert_sql = sql_text(f"""
                    INSERT INTO {collection_name}(
                    {PgVectorTableschemaEnums.TEXT.value},
                    {PgVectorTableschemaEnums.METADATA.value},
                    {PgVectorTableschemaEnums.VECTOR.value},
                    {PgVectorTableschemaEnums.CHUNK_ID.value}
                    )
                    VALUES(
                        :text,
                        :metadata,
                        :vector,
                        :chunk_id
                    )
                    """).bindparams(bindparam("metadata", type_=JSONB))

                

                    await session.execute(batch_insert_sql,values)
        

        await self.create_vector_index(collection_name=collection_name)
        return True





    async def search_by_vector(self,collection_name:str,
                                vector:List[float],
                                limit:int=5) -> List[RetrivedDocument]:



        is_collection_existed=await self.is_collection_exists(collection_name=collection_name)
        if not is_collection_existed:
            self.logger.error(f"Collection {collection_name} does not exist ,Cannot search in it")
            return False
        

        vector = "["+ ",".join([str(vector_dim) for vector_dim in vector]) + "]"

        async with self.db_client() as session:
            async with session.begin():
                search_sql=sql_text(f"""
                SELECT {PgVectorTableschemaEnums.TEXT.value} AS text,
                1-({PgVectorTableschemaEnums.VECTOR.value} <=> :vector) AS similarity
                FROM {collection_name}
                ORDER BY similarity
                LIMIT :limit
                """)

                results=await session.execute(search_sql,{"vector":vector,"limit":limit})
                results=results.fetchall()
                return [RetrivedDocument(**{"score":result.similarity,"text":result.text}) for result in results]