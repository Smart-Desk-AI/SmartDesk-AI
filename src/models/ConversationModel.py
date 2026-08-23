from .BaseDataModel import BaseDataModel
from .db_schemas import Conversation
from .enums.DataBaseEnum import DataBaseEnum

from bson.objectid import ObjectId
from pymongo import InsertOne

from sqlalchemy.future import select
from sqlalchemy import delete, func
from src.models.enums.DataBaseEnum import ConversationStatusEnum

class ConversationModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.db_client = db_client

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance

    async def create_conversation(self, project_id, conversation: Conversation):

        async with self.db_client() as session:
            async with session.begin():
                session.add(conversation)

            await session.commit()
            await session.refresh(conversation)

        return conversation

    async def get_conversation(self, project_id: int):

        async with self.db_client() as session:

            query = select(Conversation).where(
                Conversation.conversation_project_id == project_id
            )

            result = await session.execute(query)

            conversation = result.scalar_one_or_none()

            if conversation is None:
                return None
            else:
                return conversation

    async def update_conversation(self, conversation: Conversation):
        async with self.db_client() as session:
            async with session.begin():
                session.add(conversation) 
            await session.commit()
            await session.refresh(conversation)
        return conversation


    async def get_project_conversations(self, project_id: int, page_number: int = 1, page_size: int = 50):

        async with self.db_client() as session:

            skip_size = page_size * (page_number - 1)

            query = (
                select(Conversation)
                .where(
                    Conversation.conversation_project_id == project_id
                )
                .offset(skip_size)
                .limit(page_size)
            )

            result = await session.execute(query)

            conversations = result.scalars().all()

            return conversations

    async def delete_conversation(self, project_id: int):

        async with self.db_client() as session:

            query = delete(Conversation).where(
                Conversation.conversation_project_id == project_id
            )

            results = await session.execute(query)

            await session.commit()

            return results.rowcount

    async def insert_many_conversations(self, conversations: list[Conversation], batch_size: int = 100):

        async with self.db_client() as session:

            async with session.begin():

                for i in range(0, len(conversations), batch_size):

                    batch = conversations[i:i + batch_size]

                    session.add_all(batch)

            await session.commit()

        return len(conversations)


    async def close_conversation(self, project_id: int):

        async with self.db_client() as session:

            query = select(Conversation).where(
                Conversation.conversation_project_id == project_id
            )

            result = await session.execute(query)

            conversation = result.scalar_one_or_none()

            if conversation is None:
                return None
            
            conversation.status = ConversationStatusEnum.CLOSED
            await session.commit()
            await session.refresh(conversation)
            return conversation






