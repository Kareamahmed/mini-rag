from .BaseDataModel import BaseDataModel
from .db_schemes import File
from .enums.DatabaseEnums import DatabaseEnums
from bson import ObjectId


class FileModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DatabaseEnums.COLLECTION_FILE_NAME.value]

    @classmethod
    async def get_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DatabaseEnums.COLLECTION_FILE_NAME.value not in all_collections:
            indexes = File.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"], name=index["name"], unique=index["unique"]
                )

    async def insert_file(self, file: File):
        result = await self.collection.insert_one(
            file.model_dump(by_alias=True, exclude_unset=True)
        )

        file.id = result.inserted_id
        return file

    async def get_all_files(self, file_project_id: str, file_type: str):
        records = await self.collection.find(
            {
                "file_project_id": self.get_file_project_id(file_project_id),
                "file_type": file_type,
            }
        ).to_list(length=None)

        return [File(**record) for record in records]

    async def get_file_record(self, file_project_id: str, file_name: str):
        record = await self.collection.find_one(
            {
                "file_project_id": self.get_file_project_id(file_project_id),
                "file_name": file_name,
            }
        )
        if record is None:
            return None
        return File(**record)

    def get_file_project_id(self, file_project_id: str):
        return (
            ObjectId(file_project_id)
            if isinstance(file_project_id, str)
            else file_project_id
        )
