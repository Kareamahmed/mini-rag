from fastapi import APIRouter, UploadFile, status, Depends
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import aiofiles
import os
from controllers import DataController, ProjectController
from models import ResponseSignal
import logging

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])


@data_router.post("/upload/{project_id}")
async def upload_data(
    project_id: str, file: UploadFile, app_setting: Settings = Depends(get_settings)
):
    data_controller = DataController()
    # validate file properties
    is_valid, signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": signal}
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path = os.path.join(
        project_dir_path,
        data_controller.generate_unique_filename(original_filename=file.filename),
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_setting.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"error while uploading file {e}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": ResponseSignal.FILE_UPLOAD_FILED.value},
        )

    return JSONResponse(content={"message": signal})
