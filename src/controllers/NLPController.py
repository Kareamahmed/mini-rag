from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.vectordb.providers.QdrantProvider import Qdrant
from stores.llm.LLMEnums import DocumentTypeEnums
from typing import List
import json
from stores import TemplateParser


class NLPController(BaseController):
    def __init__(
        self,
        vector_db_client: Qdrant,
        generative_model,
        embedding_model,
        template_parser: TemplateParser,
    ):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.generative_model = generative_model
        self.embedding_model = embedding_model
        self.template_parser = template_parser

    async def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vector_db_client.delete_collection(
            collection_name=collection_name
        )

    async def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = await self.vector_db_client.get_collection_info(
            collection_name=collection_name
        )
        return json.loads(json.dumps(collection_info, default=lambda o: o.__dict__))

    async def index_into_vector_db(
        self, project: Project, chunks: List[DataChunk], do_reset: bool = False
    ):
        ## get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        ## create collection if not exist
        await self.vector_db_client.create_collection(
            collection_name=collection_name,
            do_reset=do_reset,
            embedding_size=self.embedding_model.embedding_size,
        )

        ## mange chunks
        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]

        vectors = [
            self.embedding_model.embed_text(
                text=text, document_type=DocumentTypeEnums.DOCUMENT.value
            )
            for text in texts
        ]

        # insert into vector_db
        await self.vector_db_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
        )
        return True

    async def search_vector_db_collection(
        self, project: Project, text: str, limit: int = 5
    ):
        # get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # embedding text
        vector = self.embedding_model.embed_text(
            text=text, document_type=DocumentTypeEnums.QUERY.value
        )
        if not vector or len(vector) == 0:
            return False

        # search
        result = await self.vector_db_client.search_by_vector(
            collection_name=collection_name, vector=vector, limit=limit
        )
        return result

    async def answer_rag_question(
        self, project: Project, query: str, chat_history: list = None, limit: int = 5
    ):
        # get related documents from vector db
        retrieved_documents = await self.search_vector_db_collection(
            project=project, text=query, limit=limit
        )
        if not retrieved_documents or len(retrieved_documents) == 0:
            return None

        # construct llm prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")

        document_prompt = "\n".join(
            [
                self.template_parser.get(
                    "rag",
                    "document_prompt",
                    {
                        "doc_num": i + 1,
                        "chunk_text": self.generative_model.process_text(doc.text),
                    },
                )
                for i, doc in enumerate(retrieved_documents)
            ]
        )
        footer_prompt = self.template_parser.get(
            "rag", "footer_prompt", {"query": query}
        )

        full_prompt = "\n\n".join([document_prompt, footer_prompt])

        answer = self.generative_model.generate_text(
            prompt=full_prompt, system_prompt=system_prompt, chat_history=chat_history
        )
        return answer, full_prompt, chat_history

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()
