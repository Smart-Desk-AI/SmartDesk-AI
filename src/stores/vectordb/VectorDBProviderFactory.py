from src.stores.vectordb.VectorDBInterface import VectorDBInterface
from src.stores.vectordb.VectorDBEnums import VectorDBEnum,DistanceMethodEnum,PgVectorDistanceMethodEnum
from src.stores.vectordb.providers.QdrantDBProvider import QdrantDBProvider
from src.stores.vectordb.providers.PGVectorProvider import PGVectorProvider
from src.controllers.BaseController import BaseController 
from sqlalchemy.orm import sessionmaker

class VectorDBProviderFactory:
    def __init__(self,config,db_client:sessionmaker=None):
        self.config=config
        self.base_controller=BaseController()
        self.db_client=db_client

    def create(self,vector_db:str=VectorDBEnum.QDRANT.value,db_path:str=None, distance_method:str=None)->VectorDBInterface:
        if vector_db==VectorDBEnum.QDRANT.value:
            return QdrantDBProvider(db_client=self.db_client, distance_method=self.config.VECTOR_DB_DISTANCE_METHOD
                                     ,index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
                                      default_vector_size=self.config.VECTOR_DB_DEFAULT_VECTOR_SIZE)
        elif vector_db==VectorDBEnum.PGVECTOR.value:
            return PGVectorProvider(db_client=self.db_client, distance_method=self.config.VECTOR_DB_DISTANCE_METHOD
                                    ,index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
                                    default_vector_size=self.config.VECTOR_DB_DEFAULT_VECTOR_SIZE)
        else:
            raise ValueError("Invalid vector db")
       

    