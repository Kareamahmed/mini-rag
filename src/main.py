from routes import base, data
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from helpers.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):

    settings = get_settings()
    app.mongo_conn = AsyncMongoClient(settings.MONGO_URL)
    app.db_client = app.mongo_conn[settings.MONGODB_DATABASE]

    yield  

    app.mongo_conn.close()



app = FastAPI(lifespan=lifespan)
app.include_router(base.base_router)
app.include_router(data.data_router)
