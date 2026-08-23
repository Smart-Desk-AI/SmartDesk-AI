from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column,String,Integer,DateTime,func,ForeignKey
from sqlalchemy.dialects.postgresql import UUID,JSONB
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from pydantic import BaseModel
from src.models.enums.DataBaseEnum import ConversationStatusEnum
from sqlalchemy import Enum




class Conversation(SQLAlchemyBase):
    __tablename__="conversations"

    conversation_id=Column(Integer,primary_key=True,autoincrement=True)
    conversation_uuid=Column(UUID(as_uuid=True),default=uuid.uuid4,unique=True,nullable=False)

    title=Column(String)
    content=Column(JSONB,nullable=False)

    created_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    updated_at=Column(DateTime(timezone=True),onupdate=func.now(),nullable=True)
    status = Column(Enum(ConversationStatusEnum),nullable=False,default=ConversationStatusEnum.ACTIVE)
    summary_ticket=Column(String)

    conversation_project_id=Column(Integer,ForeignKey('projects.project_id'),nullable=False)
    project=relationship("Project",back_populates="conversations")



    