from routes import base, data
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from helpers.config import get_settings
from stores import LLMProviderFactory


@asynccontextmanager
async def lifespan(app: FastAPI):

    settings = get_settings()
    app.mongo_conn = AsyncMongoClient(settings.MONGO_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

    llm_provider_factory = LLMProviderFactory(settings=settings)
    # generative model
    app.generative_model = llm_provider_factory.create_provider(
        provider_name=settings.GENERATION_BACKEND
    )
    app.generative_model.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    # embedding model
    app.embedding_model = llm_provider_factory.create_provider(
        provider_name=settings.EMBEDDING_BACKEND
    )
    app.embedding_model.set_embed_model(
        model_id=settings.EMBEDDING_MODEL_ID, embed_size=settings.EMBEDDING_SIZE
    )

    yield

    await app.mongo_conn.close()


app = FastAPI(lifespan=lifespan)
app.include_router(base.base_router)
app.include_router(data.data_router)
