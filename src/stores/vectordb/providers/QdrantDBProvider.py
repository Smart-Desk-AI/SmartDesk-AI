from importlib.resources import path
from typing import List
from src.stores.vectordb.VectorDBInterface import VectorDBInterface
import logging
from src.stores.vectordb.VectorDBEnums import DistanceMethodEnum
from qdrant_client import QdrantClient, models
from src.models.db_schemas import RetrivedDocument  

 

class QdrantDBProvider(VectorDBInterface):
    def __init__(self,db_client:str=None, default_vector_size:int=786,distance_method:str=None,index_threshold:int=100):
        self.db_client=db_client
        #distance method enum check 
        self.distance_method=None
        self.default_vector_size=default_vector_size
        self.index_threshold=index_threshold
        self.logger=logging.getLogger("uvicorn")
        if distance_method==DistanceMethodEnum.COSINE.value:
            self.distance_method=DistanceMethodEnum.COSINE.value
        elif distance_method==DistanceMethodEnum.DOT_PRODUCT.value:
            self.distance_method=DistanceMethodEnum.DOT_PRODUCT.value    
        else:
            self.logger.error("Invalid distance method")
            self.distance_method=DistanceMethodEnum.COSINE.value
        


        self.client=None
        
        self.logger.info("QdrantDB initialized")
        self.logger.info(f"DB Path: {self.db_client}")
        self.logger.info(f"Distance Method: {self.distance_method}")

    async def connect(self):
        if self.db_client:
            self.client=QdrantClient(path=self.db_client)
            self.logger.info("QdrantDB connected")
        else:
            self.logger.error("QdrantDB not connected")

    async def dis_connect(self):  
        self.client=None
        self.logger.info("QdrantDB disconnected")



    
    async def is_collection_exists(self,collection_name:str):
        return self.client.collection_exists(collection_name=collection_name)

    
    async def list_all_collections(self)->List[str]:
        return self.client.get_collections()
        

    async def get_collection_info(self,collection_name:str)->dict:
        return self.client.get_collection(collection_name=collection_name)


    async def create_collection(self,collection_name:str,embedding_size:int,do_reset:bool=False):
        if do_reset==1:
            await self.delete_collection(collection_name)

        if not await self.is_collection_exists(collection_name):
            self.logger.info(f"Creating new QdrantDB collection {collection_name}")
            self.client.create_collection(collection_name=collection_name,
                                                vectors_config=models.VectorParams(size=embedding_size,distance=self.distance_method))

            return True    
        else:
            self.logger.error("Collection already exists")
            return False
        
    
    async def delete_collection(self,collection_name:str):
        if await self.is_collection_exists(collection_name):
            self.client.delete_collection(collection_name=collection_name)
        else:
            self.logger.error("Collection not found")


    async def insert_one_collection(self,collection_name:str,embedding:List[float],metadata:dict=None,record_id:str=None):
        if await self.is_collection_exists(collection_name):
            self.client.upload_records(collection_name=collection_name,
                                records=[models.Record(id=record_id,vector=embedding,payload=metadata)])

            self.logger.info("Point inserted successfully")
            return True    
        else:
            self.logger.error("Collection not found")
            return False

    
    
    async def insert_many_collections(self,collection_name:str,texts:list=None,vectors:list=None,metadata:List[dict]=None,record_ids:List[str]=None,batch_size:int=50):

        if metadata is None:
            metadata=[None] * len(vectors)

        if record_ids is None:
            record_ids=list(range(0,len(texts)))
        

        


        if self.is_collection_exists(collection_name=collection_name):

            for i in range(0,len(texts),batch_size):
                batch_end=i+batch_size

                try:
                    self.client.upload_records(
                        collection_name=collection_name,
                        records=[
                            models.Record(
                                id=record_ids[j],
                                vector=vectors[j],
                                payload={"text": texts[j], **(metadata[j] or {})}
                            )
                            for j in range(i, min(batch_end, len(texts)))
                        ]
                    )
                except Exception as e:
                    self.logger.error(e)
                    return False

            return True    
        else:
            self.logger.error("Collection not found")
            return False


    
    
    
    async def serach_by_vector(self,collection_name:str,vector:List[float],limit:int=5):
        
        if await self.is_collection_exists(collection_name=collection_name):
            results=self.client.search(collection_name=collection_name,query_vector=vector,limit=limit) 
            return [RetrivedDocument(**{"score":result.score,"text":result.payload["text"]}) for result in results]   
        else:
            self.logger.error("Collection not found")
            return False 



