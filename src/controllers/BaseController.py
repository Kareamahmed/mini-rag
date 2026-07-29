from helpers.config import get_settings, Settings
import os


class BaseController:
    def __init__(self):
        self.app_settings: Settings = get_settings()
        self.base_dir = os.path.dirname(
            os.path.dirname(__file__)
        )  # get the base dirc of this file "src"
        self.files_dir = os.path.join(self.base_dir, "assets/files")

        self.vector_db_dir = os.path.join(self.base_dir, "assets/vector_db")

    def get_vector_db_path(self, db_path: str):
        vector_db_path = os.path.join(self.vector_db_dir, db_path)
        if not os.path.exists(vector_db_path):
            os.makedirs(vector_db_path)

        return vector_db_path
