from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.vectordb.providers.Qdrant import Qdrant
from stores.llm.LLMEnums import DocumentTypeEnums
from typing import List
import json


class NLPController(BaseController):
    def __init__(self, vector_db_client: Qdrant, generative_model, embedding_model):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.generative_model = generative_model
        self.embedding_model = embedding_model

    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vector_db_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = self.vector_db_client.get_collection_info(
            collection_name=collection_name
        )
        return json.loads(json.dumps(collection_info, default=lambda o: o.__dict__))

    def index_into_vector_db(
        self, project: Project, chunks: List[DataChunk], do_reset: bool = False
    ):
        ## get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        ## create collection if not exist
        self.vector_db_client.create_collection(
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
        self.vector_db_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
        )
        return True

    def search_vector_db_collection(self, project: Project, text: str, limit: int = 5):
        # get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # embedding text
        vector = self.embedding_model.embed_text(
            text=text, document_type=DocumentTypeEnums.QUERY.value
        )
        if not vector or len(vector) == 0:
            return False

        # search
        result = self.vector_db_client.search_by_vector(
            collection_name=collection_name, vector=vector, limit=limit
        )
        return json.loads(json.dumps(result, default=lambda o: o.__dict__))

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()
