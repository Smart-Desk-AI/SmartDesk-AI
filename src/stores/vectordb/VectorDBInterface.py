from abc import ABC , abstractmethod
from typing import List
from src.models.db_schemas import RetrivedDocument  

class VectorDBInterface(ABC):
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def dis_connect(self):
        pass
    
    
    @abstractmethod
    def is_collection_exists(self,collection_name:str)->bool:
        pass


    @abstractmethod
    def list_all_collections(self)->list:
        pass 
    
    @abstractmethod
    def get_collection_info(self,collection_name:str)-> dict:
        pass


    @abstractmethod
    def create_collection(self,collection_name:str,embedding_size:int,do_reset:bool=False):
        pass
    

    
    @abstractmethod
    def delete_collection(self,collection_name:str):
        pass

    @abstractmethod
    def insert_one_collection(self,collection_name:str,embedding:List[float],metadata:dict=None,record_id:str=None):
        pass

    @abstractmethod
    def insert_many_collections(self,collection_name:str,texts:list=None,vectors:list=None,metadata:list=None,record_ids:list=None,batch_size:int=50):
        pass

    @abstractmethod
    def search_by_vector(self,collection_name:str,vector:List[float],limit:int=5)->List[RetrivedDocument]:
        pass
    