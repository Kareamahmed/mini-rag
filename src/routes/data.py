from fastapi import APIRouter, UploadFile, status, Depends
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import aiofiles
import os
from controllers import DataController, ProjectController, ProcessController
from models import ResponseSignal
import logging
from .schemes.data import ProcessRequest

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

    file_id = data_controller.generate_unique_filename(original_filename=file.filename)
    file_path = os.path.join(
        project_dir_path,
        file_id,
    )

    # write the file
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

    return JSONResponse(content={"message": signal, "file_id": file_id})


@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: ProcessRequest):

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)
    chunks = process_controller.get_file_chunks(
        file_content=file_content, chunk_size=chunk_size, chunk_overlap=overlap_size
    )

    if chunks is None or len(chunks) == 0:
        return JSONResponse(
            content={
                "message": ResponseSignal.PROCESSING_FAILED.value,
                "file_id": file_id,
            }
        )

    return chunks
