from ..LLMInterface import LLMInterface
from ..LLMEnums import GoogleEnums
from google import genai
from google.genai import types
import logging


class GeminiProvider(LLMInterface):

    def __init__(
        self,
        api_key: str,
        max_input_tokens: int = 5000,
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

        self.client = genai.Client(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        self.enums = GoogleEnums

    def generate_text(
        self,
        prompt: str,
        system_prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temperature: float = None,
    ):

        if not self.client:
            self.logger.error("Gemini client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini client was not set")
            return None

        max_output_tokens = (
            max_output_tokens if max_output_tokens else self.default_max_input_tokens
        )

        temperature = temperature if temperature else self.temperature

        chat_history.append(
            self.construct_prompt(prompt=prompt, role=GoogleEnums.USER.value)
        )

        interaction = self.client.interactions.create(
            model=self.generation_model_id,
            input=chat_history,
            system_instruction=system_prompt,
            store=False,
            generation_config={
                "max_output_tokens": max_output_tokens,
                "temperature": temperature,
            },
        )

        if not interaction or not interaction.output_text:
            self.logger.error("Error while generating text with Gemini")
            return None

        for step in interaction.steps:
            chat_history.append(step.model_dump())

        return interaction.output_text, chat_history

    def embed_text(self, text, document_type=None):

        if not self.client:
            self.logger.error("Gemini client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini client was not set")
            return None

        result = self.client.models.embed_content(
            model=self.embedding_model_id,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=self.embedding_size),
            # config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
        )

        if not result or not result.embeddings:
            self.logger.error("Error while embedding text with Gemini")
            return None

    def construct_prompt(self, prompt: str, role: str):
        return {
            "type": role,
            "content": [{"type": "text", "text": prompt}],
        }

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embed_model(self, model_id, embed_size):
        self.embedding_model_id = model_id
        self.embedding_size = embed_size

    def process_text(self, text: str):
        return text[: self.default_max_input_tokens].strip()
