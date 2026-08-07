from routes import base, data, nlp
from contextlib import asynccontextmanager
from fastapi import FastAPI
from helpers.config import get_settings
from stores import LLMProviderFactory, VectorDBFactory, TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI):

    settings = get_settings()
    app.postgres_engine = create_async_engine(
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    )
    app.db_client = sessionmaker(app.postgres_engine, class_=AsyncSession, expire_on_commit=False)

    llm_provider_factory = LLMProviderFactory(settings=settings)
    vector_db_provider_factory = VectorDBFactory(settings=settings)
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
    # vector db
    app.vector_db_client = vector_db_provider_factory.create_provider(
        provider_name=settings.VECTOR_DB_BACKEND
    )
    app.vector_db_client.connect()

    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG, default_language=settings.DEFAULT_LANG
    )
    yield

    app.postgres_engine.dispose()
    app.vector_db_client.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
