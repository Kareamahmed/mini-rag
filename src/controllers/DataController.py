from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignal
import uuid
from pathlib import Path


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576  # convert MB to byte

    def validate_uploaded_file(self, file: UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILL_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value

    def generate_unique_filename(self, original_filename: str) -> str:
        # Remove special characters from original filename
        safe_name = "".join(
            c
            for c in Path(original_filename).stem
            if c.isalnum() or c in ("-", "_", " ")
        )
        file_extension = Path(original_filename).suffix

        # Generate unique filename
        unique_name = f"{safe_name}_{uuid.uuid4().hex[:8]}{file_extension}"
        return unique_name
