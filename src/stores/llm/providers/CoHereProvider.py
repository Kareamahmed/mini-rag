from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums, DocumentTypeEnums
import cohere
import logging


class CoHereProvider(LLMInterface):

    def __init__(
        self,
        api_key: str,
        max_input_tokens: int = 1000,
        max_output_tokens: int = 1000,
        temperature: float = 0.0,
    ):
        self.api_key = api_key
        self.default_max_input_tokens = max_input_tokens
        self.default_max_output_tokens = max_output_tokens
        self.temperature = temperature

        self.generation_model_id = None  # change at run time
        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.ClientV2(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        self.enums = CoHereEnums

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temperature: float = None,
    ):

        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for CoHere client was not set")
            return None

        max_output_tokens = (
            max_output_tokens if max_output_tokens else self.default_max_output_tokens
        )

        temperature = temperature if temperature else self.temperature

        chat_history.append(
            self.construct_prompt(prompt=prompt, role=CoHereEnums.USER.value)
        )

        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature,
        )

        if (
            not response
            or not response.message
            or not response.message.content
            or len(response.message.content) == 0
        ):
            self.logger.error("Error while generating text with CoHere")
            return None

        generated_text = response.message.content[0].text

        return generated_text

    def embed_text(self, text, document_type=None):

        if not self.client:
            self.logger.error("CoHere client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for CoHere client was not set")
            return None

        input_type = CoHereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnums.QUERY.value:
            input_type = CoHereEnums.QUERY.value


        response = self.client.embed(
            model=self.embedding_model_id,
            texts=[text],
            input_type=input_type,
            output_dimension=self.embedding_size,
        )

        if (
            not response
            or not response.embeddings
            or not response.embeddings.float
        ):
            self.logger.error("Error while embedding text with CoHere")
            return None

        return  response.embeddings.float[0]

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": prompt,
        }

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embed_model(self, model_id, embed_size):
        self.embedding_model_id = model_id
        self.embedding_size = embed_size

    def process_text(self, text: str):
        return text[: self.default_max_input_tokens].strip()