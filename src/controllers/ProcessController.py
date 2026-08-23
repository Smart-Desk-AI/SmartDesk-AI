"""
Document processing controller for the SmartDesk AI application.

This module provides the `ProcessController` class, which handles the extraction
and chunking of text from uploaded documents (like PDFs) to prepare them for
vector embedding and retrieval-augmented generation (RAG).
"""
from .BaseController import BaseController
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from typing import List
from dataclasses import dataclass

@dataclass
class Document:
    page_content:str
    metadata:List[dict]

class ProcessController(BaseController):
    """
    Controller responsible for processing and chunking document content.

    This class provides methods to load documents from the filesystem and split
    their content into smaller, overlapping chunks suitable for semantic search
    and vector database ingestion.
    """

    def __init__(self, project_id: str = None):
        """
        Initializes the ProcessController.

        Args:
            project_id (str, optional): The ID of the project whose files
                will be processed. Defaults to None.
        """
        super().__init__()
        self.project_id = project_id

    def get_file_content(self, file_id: str):
        """
        Retrieves and loads the content of a specific file within the project.

        Args:
            file_id (str): The unique identifier (filename) of the file to load.

        Returns:
            list[Document] | None: A list of LangChain Document objects if the file
                exists and is successfully loaded; otherwise, None.
        """
        file_path = os.path.join(
            self.files_dir,
            str(self.project_id),
            file_id
        )

        if not os.path.exists(file_path):
            return None

        return self.load_pdf(file_path)

    def load_pdf(self, path: str):
        """
        Loads a PDF file from the filesystem.

        Uses LangChain's PyPDFLoader to parse the PDF and extract its text
        along with page-level metadata.

        Args:
            path (str): The absolute or relative path to the PDF file.

        Returns:
            list[Document]: A list of LangChain Document objects representing the PDF pages.
        """
        pdf_loader = PyPDFLoader(path)

        return pdf_loader.load() 

    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int=100, overlap_size: int=20):

        file_content_texts = [
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]

        # chunks = text_splitter.create_documents(
        #     file_content_texts,
        #     metadatas=file_content_metadata
        # )

        chunks = self.process_simpler_splitter(
            texts=file_content_texts,
            metadatas=file_content_metadata,
            chunk_size=chunk_size,
        )

        return chunks

    
    
    
    def split_text_into_chunks(self, document: list, chunk_size: int, chunk_overlap: int):
        """
        Splits a large document into smaller, overlapping chunks.

        This function divides the input document into segments to ensure that
        context is preserved across chunk boundaries (via overlap) while keeping
        the chunks small enough for the embedding model's context window.

        Args:
            document (list): List of LangChain Document objects to split.
            chunk_size (int): Maximum number of characters per chunk.
            chunk_overlap (int): Number of overlapping characters between chunks.

        Returns:
            list[Document]: A list containing the newly generated document chunks.
        """
        # Configure the text splitter to prioritize natural breaks (paragraphs, lines, words)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Separate content and metadata to maintain metadata linkage after splitting
        doc_content_list = [doc.page_content for doc in document]
        doc_metadata_list = [doc.metadata for doc in document]

        chunks = text_splitter.create_documents(doc_content_list, metadatas=doc_metadata_list) 

        print(f"Number of chunks: {len(chunks)}")
        return chunks



    def process_simpler_splitter(self,texts:List[str],metadatas:List[dict],chunk_size:int,splitter_tag:str="\n"):
            full_text=" ".join(texts)

            lines=[doc.strip() for doc in full_text.split(splitter_tag)if len(doc.strip())>1]

            chunks=[]
            current_chunk=""


            for line in lines:
                current_chunk+=line+splitter_tag
                if len(current_chunk)>chunk_size:
                    chunks.append(Document(current_chunk.strip(),metadata=metadatas))
                    current_chunk=""


            if len(current_chunk)>0:
                chunks.append(Document(current_chunk.strip(),metadata=metadatas))



            return chunks

            




            
                




