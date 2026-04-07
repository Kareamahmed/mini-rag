from fastapi import APIRouter, UploadFile , status 
from fastapi.responses import JSONResponse
from controllers import DataController , ProjectController

data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])


@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile):

    # validate file properties
    is_valid , signal = DataController().validate_uploaded_file(file=file)
    
    if not is_valid:
        return JSONResponse(
            status_code =status.HTTP_400_BAD_REQUEST,
            content = {"message": signal}
        )
    
    project_dir_path = ProjectController().get_project_path(project_id=project_id)