from helpers.config import Settings
from .providers.Qdrant import Qdrant
from controllers.BaseController import BaseController
from VectorDBEnums import VectorDBEnums


class VectorDBFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_controller = BaseController()

    def create_provider(self, provider_name: str):
        if provider_name == VectorDBEnums.QDRANT.value:
            return Qdrant(
                db_path=self.base_controller.get_vector_db_path(
                    db_path=self.settings.VECTOR_DB_PATH
                ),
                distance_metric=self.settings.VECTOR_DISTANCE_METRIC,
            )
        return None
