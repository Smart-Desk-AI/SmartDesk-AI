# pyrefly: ignore [missing-import]
"""
Configuration management for the SmartDesk AI application.

This module utilizes Pydantic's BaseSettings to load, validate, and manage
environment variables and application-level settings.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings model powered by Pydantic.

    This class automatically reads environment variables from the `.env` file
    and performs type casting and validation based on the defined type hints.

    Attributes:
        APP_NAME (str): The name of the application.
        VERSION (str): The current application version.
        OPEN_API_KEYS (str): Comma-separated API keys, if applicable.
        FILE_DEFAULT_CHUNK_SIZE (int): The default chunk size (in bytes) used
            for streaming file uploads to prevent memory overload. Defaults to 1 MB.
        MONGODB_URL (str): The connection string for the MongoDB database.
        MONGODB (str): The specific database name to use within MongoDB.
    """
    APP_NAME:str
    VERSION:str
    OPEN_API_KEYS:str
    FILE_DEFAULT_CHUNK_SIZE:int


    POSTGRES_USERNAME:str
    POSTGRES_PASSWORD:str
    POSTGRES_HOST:str
    POSTGRES_PORT:int
    POSTGRES_MAIN_DATABASE:str


# ==========LLM Config ================

    GENERATION_BACKEND:str
    EMBEDDING_BACKEND:str

    # ========== OPENAI Config ============
    OPEN_API_KEYS:str
    OPEN_API_URL:str

    # ========== COHERE Config ============
    COHERE_API_KEY:str

    GENERATION_BACKEND_LITERAL:List[str]=None
    GENERATION_MODEL_ID:str
    EMBEDDING_MODEL_ID:str
    EMBEDDING_MODEL_SIZE:str

    INPUT_DEFAULT_MAX_CHARACTERS:int
    GENERATION_DEFAULT_MAX_TOKENS:int
    GENERATION_DEFAULT_TEMPERATURE:float

    # ==========VECTOR DB Config ===========
    VECTOR_DB_BACKEND_LITERAL:List[str]=None
    VECTOR_DB_BACKEND:str
    VECTOR_DB_PATH:str
    VECTOR_DB_DISTANCE_METHOD:str 
    VECTOR_DB_PGVEC_INDEX_THRESHOLD:int
    VECTOR_DB_DEFAULT_VECTOR_SIZE:int
 
    
    DEFAULT_LANGUAGE:str="en"

    PRIMARY_LANGUAGE:str="en"

    # ========== SMTP Config ==========
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = None
    SMTP_PASSWORD: str = None
    SMTP_SENDER: str = None
    SMTP_USE_TLS: bool = True


    class Config:
        env_file=".env"



def get_settings():
    """
    Retrieves a validated instance of the application settings.

    This function instantiates the `Settings` class, triggering the load
    and validation of the `.env` file. It can be used as a FastAPI dependency.

    Returns:
        Settings: The populated configuration object.
    """
    return Settings()
