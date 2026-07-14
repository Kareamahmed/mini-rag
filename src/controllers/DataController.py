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

        if (
            file.size > self.app_settings.FILL_MAX_SIZE * self.size_scale
        ):  # "file.size" return size in byte
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value


    def generate_unique_filename(self, original_filename: str) -> str:
        stem = Path(original_filename).stem
        safe_name = "".join(c for c in stem if c.isalnum() or c in ("_", "-"))
        safe_name = safe_name[:100] or "file"

        file_extension = Path(original_filename).suffix.lower()

        unique_name = f"{safe_name}_{uuid.uuid4().hex[:8]}{file_extension}"
        return unique_name
