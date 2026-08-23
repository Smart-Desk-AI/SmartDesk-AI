"""
Enumerations for database collections.

This module provides standard definitions for the names of MongoDB collections
used throughout the application, ensuring consistency across models.
"""
from enum import Enum


class DataBaseEnum(Enum):
    """
    Standardizes MongoDB collection names.

    Using this enumeration prevents hardcoded strings in model initialization,
    making it easier to rename collections in the future if necessary.

    Attributes:
        COLLECTION_PROJECT_NAME: The collection storing project documents.
        COLLECTION_CHUNK_NAME: The collection storing text chunks for RAG.
        COLLECTION_ASSET_NAME: The collection storing file and resource assets.
    """
    COLLECTION_PROJECT_NAME = 'projects'
    COLLECTION_CHUNK_NAME = 'chunks'
    COLLECTION_ASSET_NAME = 'assets'

class ConversationStatusEnum(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
