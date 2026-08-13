from helpers.config import Settings
from .providers.QdrantProvider import QdrantProvider
from .providers.PGVectorProvider import PGVectorProvider
from controllers.BaseController import BaseController
from .VectorDBEnums import VectorDBEnums
from sqlalchemy.orm import sessionmaker


class VectorDBFactory:
    def __init__(self, settings: Settings, db_client: sessionmaker = None):
        self.settings = settings
        self.base_controller = BaseController()
        self.db_client = db_client

    def create_provider(self, provider_name: str):
        if provider_name == VectorDBEnums.QDRANT.value:
            return QdrantProvider(
                db_path=self.base_controller.get_vector_db_path(
                    db_path=self.settings.VECTOR_DB_PATH
                ),
                distance_metric=self.settings.VECTOR_DISTANCE_METRIC,
            )
        if provider_name == VectorDBEnums.PGVECTOR.value:
            return PGVectorProvider(
                db_client=self.db_client,
                distance_metric=self.settings.VECTOR_DISTANCE_METRIC,
                index_threshold=self.settings.VECTOR_DB_PGVECT_INDEX_THRESHOLD,
                default_vector_size=self.settings.EMBEDDING_SIZE,
            )
        return None
