"""
Main application entry point for SmartDesk AI.

This module initializes the FastAPI application, loads environment variables,
establishes the database connection to MongoDB, and registers the application routes.
It serves as the central hub tying the project's infrastructure and routing together.
"""
import os
from fastapi import FastAPI
from dotenv import load_dotenv

# =====================================================
# Load Environment Variables
# =====================================================
# Load environment variables before importing other project modules
# to ensure configurations like MongoDB URI are available.
load_dotenv("src/.env")

from src.routes import base, data,nlp,conversation
from src.helpers import config
from src.stores.llm.LLMProviderFactory import LLMProviderFactory
from src.stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from src.stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.utils.metrics import setup_metrics



from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


setup_metrics(app)


# =====================================================
# Application Lifespan Events
# =====================================================


async def start_up_span():
    """
    Handles application startup operations.

    This function is triggered when the FastAPI server starts. It reads the
    application settings and establishes an asynchronous connection to the 
    MongoDB database, attaching the client and database instances to the 
    app state for global access.
    """
    settings = config.get_settings()

    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    app.db_engine=create_async_engine(postgres_conn,echo=True)

    app.db_client=sessionmaker(app.db_engine,class_=AsyncSession,expire_on_commit=False)
    
    
    llm_provider_factory = LLMProviderFactory(config=settings)
       

    #generation_client
    app.generation_client = llm_provider_factory.create(settings.GENERATION_BACKEND)  

    #embedding_client
    app.embedding_client = llm_provider_factory.create(settings.EMBEDDING_BACKEND)

    #set generation model
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    
    #set embedding model
    app.embedding_client.set_embeddings_model(settings.EMBEDDING_MODEL_ID,settings.EMBEDDING_MODEL_SIZE)


    #vector_db_client

    vectordb_provider_factory=VectorDBProviderFactory(config=settings,db_client=app.db_client)
    app.vectordb_client = vectordb_provider_factory.create(vector_db=settings.VECTOR_DB_BACKEND)
    await app.vectordb_client.connect()

    app.template_parser=TemplateParser(language=settings.PRIMARY_LANGUAGE,default_language=settings.DEFAULT_LANGUAGE)


    





    
    



    print("Connected to MongoDB")


async def shutdown_span():
    """
    Handles application shutdown operations.

    This function is triggered when the FastAPI server stops. It ensures
    that the MongoDB connection is properly closed to prevent connection leaks.
    """
    app.db_engine.dispose()
    print("Closed MongoDB connection")  
    await app.vectordb_client.disconnect()
    print("Closed VectorDB connection")




# =====================================================
# Route Registration
# =====================================================
#app.router.lifespan.on_startup.append(start_up_span)
#app.router.lifespan.on_shutdown.append(shutdown_span)

app.on_event("startup")(start_up_span)
app.on_event("shutdown")(shutdown_span)


# Register the base routes (e.g., health checks or general endpoints)
app.include_router(base.base_router)

# Register data processing routes (e.g., upload, process, chunks)
app.include_router(data.data_router)


app.include_router(nlp.nlp_router)

app.include_router(conversation.conversation_router)

@app.get("/")
def home():
    """
    Root endpoint for the SmartDesk AI API.

    Provides a simple heartbeat check to verify the API is running
    and accessible.

    Returns:
        dict: A welcome message indicating the API status.
    """
    return {"message": "SmartDesk AI API is running"}
