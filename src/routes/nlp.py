from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schemes.nlp import PushRequest, SearchRequest
import logging
from models import ProjectModel, ChunkModel
from controllers import NLPController
from models import ResponseSignal

nlp_router = APIRouter(prefix="/api/v1/nlp", tags=["api_v1", "nlp"])
logger = logging.getLogger("uvicorn.error")


## push
@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):
    # get the project
    db_client = request.app.db_client
    project_model = await ProjectModel.get_instance(db_client=db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value,
            },
        )
    nlp_controller = NLPController(
        vector_db_client=request.app.vector_db_client,
        generative_model=request.app.generative_model,
        embedding_model=request.app.embedding_model,
        template_parser=request.app.template_parser,
    )
    chunk_model = await ChunkModel.get_instance(db_client=db_client)

    has_records = True
    page_no = 1
    inserted_item_counts = 0
    while has_records:
        # get page_chunks
        page_chunks = await chunk_model.get_chunks_by_project_id(
            chunk_project_id=project.project_id, page_no=page_no
        )

        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break
        else:
            page_no += 1

        is_inserted = nlp_controller.index_into_vector_db(
            project=project, chunks=page_chunks, do_reset=push_request.do_reset
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value,
                },
            )
        inserted_item_counts += len(page_chunks)

    return JSONResponse(
        content={
            "message": ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value,
            "inserted_counts": inserted_item_counts,
        },
    )


## info
@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
    # get the project
    db_client = request.app.db_client
    project_model = await ProjectModel.get_instance(db_client=db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vector_db_client=request.app.vector_db_client,
        generative_model=request.app.generative_model,
        embedding_model=request.app.embedding_model,
        template_parser=request.app.template_parser,
    )

    collection_info = nlp_controller.get_vector_db_collection_info(project=project)

    if not collection_info:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": ResponseSignal.VECTOR_DB_COLLECTION_INFO_NOT_FOUND.value,
            },
        )

    return JSONResponse(
        content={
            "message": ResponseSignal.VECTOR_DB_COLLECTION_INFO.value,
            "collection_info": collection_info,
        },
    )


## search
@nlp_router.post("/index/search/{project_id}")
async def search_index(
    request: Request, project_id: int, search_request: SearchRequest
):

    db_client = request.app.db_client
    project_model = await ProjectModel.get_instance(db_client=db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vector_db_client=request.app.vector_db_client,
        generative_model=request.app.generative_model,
        embedding_model=request.app.embedding_model,
        template_parser=request.app.template_parser,
    )
    text = search_request.text
    limit = search_request.limit

    results = nlp_controller.search_vector_db_collection(
        project=project, text=text, limit=limit
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": ResponseSignal.VECTOR_DB_SEARCH_COLLECTION_ERROR.value,
            },
        )
    return JSONResponse(
        content={
            "message": ResponseSignal.VECTOR_DB_SEARCH_COLLECTION_SUCCESS.value,
            "retrieved_chunks": [result.model_dump() for result in results],
        },
    )


## answer
@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: int, search_request: SearchRequest):

    db_client = request.app.db_client

    project_model = await ProjectModel.get_instance(db_client=db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vector_db_client=request.app.vector_db_client,
        generative_model=request.app.generative_model,
        embedding_model=request.app.embedding_model,
        template_parser=request.app.template_parser,
    )
    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit,
        chat_history=[],
    )

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": ResponseSignal.RAG_ANSWER_ERROR.value,
            },
        )

    return JSONResponse(
        content={
            "message": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history,
        },
    )
