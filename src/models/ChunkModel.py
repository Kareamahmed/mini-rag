from .BaseDataModel import BaseDataModel
from .enums.DatabaseEnums import DatabaseEnums
from .db_schemes import DataChunk
from bson import ObjectId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):

    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DatabaseEnums.COLLECTION_CHUNK_NAME.value]

  
    @classmethod
    async def get_instance(cls, db_client: object):
        instance = cls(db_client=db_client) # cls == ProjectModel
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DatabaseEnums.COLLECTION_CHUNK_NAME.value not in all_collections:
            indexes = DataChunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"], name=index["name"], unique=index["unique"]
                )

    async def insert_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(
            chunk.model_dump(by_alias=True, exclude_unset=True)
        )
        chunk.id = result.inserted_id
        return chunk

    async def get_chunk(self, chunk_id: str):
        result = await self.collection.find_one({"_id": ObjectId(chunk_id)})

        if result is None:
            return None

        return DataChunk(**result)

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            operations = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True))
                for chunk in batch
            ]

            await self.collection.bulk_write(operations)
        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: str):
        result = await self.collection.delete_many({"chunk_project_id": ObjectId(project_id)})
        return result.deleted_count
