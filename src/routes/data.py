from fastapi import APIRouter, UploadFile, status, Depends, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import aiofiles
import os
from controllers import DataController, ProjectController, ProcessController
from models import ResponseSignal, ProjectModel, ChunkModel
import logging
from .schemes.data import ProcessRequest
from models.db_schemes import DataChunk

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])


@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: str,
    file: UploadFile,
    app_setting: Settings = Depends(get_settings),
):
    # database
    project_model = ProjectModel(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

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
async def process_endpoint(
    request: Request, project_id: str, process_request: ProcessRequest
):

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    reset = process_request.do_reset
    # database
    project_model = ProjectModel(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    chunk_model = ChunkModel(db_client=request.app.db_client)

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

    chunks_records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i + 1,
            chunk_project_id=project.id,
        )
        for i, chunk in enumerate(chunks)
    ]

    if reset == 1:
        deleted_count = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )
        return deleted_count
    
    
    no_records = await chunk_model.insert_many_chunks(chunks=chunks_records)
    return JSONResponse(
        content={
            "message": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_records": no_records,
        }
    )
