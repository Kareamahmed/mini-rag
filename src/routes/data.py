from fastapi import APIRouter, UploadFile, status, Depends, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import aiofiles
import os
from controllers import DataController, ProjectController, ProcessController
from models import ResponseSignal, ProjectModel, ChunkModel, AssetModel, AssetTypeEnums
import logging
from .schemes.data import ProcessRequest
from models.db_schemes import DataChunk, Asset
from controllers import NLPController

logger = logging.getLogger("uvicorn.error")
data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])


@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: int,
    file: UploadFile,
    app_setting: Settings = Depends(get_settings),
):
    # database
    db_client = request.app.db_client
    project_model = await ProjectModel.get_instance(db_client=db_client)
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

    # store file into database
    asset_model = await AssetModel.get_instance(db_client=db_client)
    asset_record = await asset_model.insert_asset(
        Asset(
            asset_project_id=project.project_id,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path),
            asset_type=AssetTypeEnums.FILE.value,
        )
    )

    return JSONResponse(
        content={"message": signal, "file_id": str(asset_record.asset_name)}
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(
    request: Request, project_id: int, process_request: ProcessRequest
):

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    reset = process_request.do_reset

    # database
    db_client = request.app.db_client
    project_model = await ProjectModel.get_instance(db_client=db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)
    chunk_model = await ChunkModel.get_instance(db_client=db_client)
    asset_model = await AssetModel.get_instance(db_client=db_client)

    nlp_controller = NLPController(
        vector_db_client=request.app.vector_db_client,
        generative_model=request.app.generative_model,
        embedding_model=request.app.embedding_model,
        template_parser=request.app.template_parser,
    )

    if reset == 1:
        # delete vectors
        collection_name = nlp_controller.create_collection_name(
            project_id=project.project_id
        )
        _ = await request.app.vector_db_client.delete_collection(
            collection_name=collection_name
        )
        # delete chunks
        deleted_count = await chunk_model.delete_chunks_by_project_id(
            project_id=project.project_id
        )
        return deleted_count

    project_files_ids = {}
    if process_request.file_name:
        record = await asset_model.get_asset_record(
            asset_project_id=project.project_id, asset_name=process_request.file_name
        )
        if record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": ResponseSignal.FILE_ID_ERROR.value,
                },
            )
        project_files_ids = {record.asset_id: record.asset_name}
    else:
        project_assets = await asset_model.get_assets_by_project_id(
            asset_project_id=project.project_id, asset_type=AssetTypeEnums.FILE.value
        )
        project_files_ids = {
            asset.asset_id: asset.asset_name for asset in project_assets
        }

    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": ResponseSignal.NO_FILES_ERROR.value,
            },
        )

    process_controller = ProcessController(project_id=project_id)

    ###
    no_records = 0
    no_files = 0
    for asset_id, asset_name in project_files_ids.items():

        file_content = process_controller.get_file_content(file_id=asset_name)
        # check  file already exists in your project_path under assets/files
        if file_content is None:
            logger.error(f"Error While Processing File : {asset_name}")
            continue

        chunks = process_controller.get_file_chunks(
            file_content=file_content, chunk_size=chunk_size, chunk_overlap=overlap_size
        )

        if chunks is None or len(chunks) == 0:
            return JSONResponse(
                content={
                    "message": ResponseSignal.PROCESSING_FAILED.value,
                    "file_id": asset_name,
                }
            )

        chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i + 1,
                chunk_project_id=project.project_id,
                chunk_asset_id=asset_id,
            )
            for i, chunk in enumerate(chunks)
        ]

        no_records += await chunk_model.insert_many_chunks(chunks=chunks_records)
        no_files += 1

    return JSONResponse(
        content={
            "message": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_records": no_records,
            "processed_files": no_files,
        }
    )
