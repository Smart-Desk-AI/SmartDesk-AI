from src.stores.llm.LLMInterface import LLMInterface
import logging
from src.stores.llm.LLMEnums import COHEREEnums ,DocumentTypeEnum  
import cohere
from typing import List,Union


class CohereProvider(LLMInterface):
    def __init__(self,api_key:str,
                default_input_max_characters:int=1000,
                default_output_max_characters:int=1000,
                default_tempreture:float=0.1):
        self.api_key=api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_output_max_characters = default_output_max_characters
        self.default_tempreture = default_tempreture

        self.generation_model_id=None
        self.embeddings_model_id=None
        self.embedding_size=None

        self.logger=logging.getLogger(__name__)
        self.enums=COHEREEnums

        # Only initialize the client if an API key is provided
        self.client = None
        if self.api_key and len(self.api_key) > 0:
            self.client = cohere.Client(api_key=self.api_key)
        else:
            self.logger.warning("Cohere API key is not set. Client will not be initialized.")


    def set_generation_model(self, model_id:str) -> None:
        self.generation_model_id = model_id

    def set_embeddings_model(self, model_id:str,embedding_size:int) -> None:  
        self.embeddings_model_id = model_id   
        self.embedding_size = embedding_size 


    def process_text(self,text:str) -> str:
        return text[:self.default_input_max_characters].strip()
    

    def generate_text(self, prompt:str,chat_history:list=[],max_output_tokens:int=None,temprature:float=None) -> str:
        if not self.client:
            self.logger.error("Cohere client is not initialized")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model id is not set")
            return None

        max_tokens=max_output_tokens if max_output_tokens else self.default_output_max_characters
        temprature=temprature if temprature else self.default_tempreture
        chat_history.append(self.construct_prompt(prompt))

        response = self.client.chat(
            model=self.generation_model_id,
            chat_history=chat_history,
            message=self.process_text(prompt),
            max_tokens=max_tokens,
            temperature=temprature
        )

        if not response or not response.text or len(response.text)==0 :
            self.logger.error("No response from Cohere client")
            return None

        return response.text




    def embed_text(self, text:Union[str,List[str]],document_type:str=None) -> list[float]:
        if not self.client:
            self.logger.error("Cohere client is not initialized")
            return None

        if isinstance(text,str):
            text=[text]

        if not self.embeddings_model_id:
            self.logger.error("Embeddings model id is not set")
            return None

        input_type=COHEREEnums.DOCUMENT.value
        if document_type==DocumentTypeEnum.QUERY:
            input_type=COHEREEnums.QUERY.value



        response = self.client.embed(
            model=self.embeddings_model_id,
            texts=[self.process_text(t) for t in text],
            input_type=input_type
        )

        if not response or not response.embeddings:
            self.logger.error("No Embeddings generated from Cohere client")
            return None

        return [f for f in response.embeddings]
        


    def construct_prompt(self, prompt: str, role: str="user") -> dict:
        return {'role': role, 'message': prompt}
