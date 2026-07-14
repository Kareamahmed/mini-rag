from helpers.config import get_settings, Settings
import os


class BaseController:
    def __init__(self):
        self.app_settings: Settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__)) # get the base dirc of this file "src"
        self.files_dir = os.path.join(self.base_dir, "assets/files")
