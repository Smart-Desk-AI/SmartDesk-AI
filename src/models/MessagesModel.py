from .BaseDataModel import BaseDataModel
from .db_schemas import Conversation
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne
from sqlalchemy.future import select
from sqlalchemy import delete,func





class MessagesModel(BaseDataModel):
    
    
    
    def __init__(self, db_client: object):


        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):

        instance = cls(db_client)
        return instance 



    async def create_message(self,project_id,message:str):
        pass




    async def get_message(self,message_id:int):
        pass


    async def get_project_messages(self,project_id:int):
        pass


    async def delete_message(self,message_id:int):
        pass

    async def insert_many_messages(self,messages:list):
        pass



                
