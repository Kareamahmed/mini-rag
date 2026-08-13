from .BaseDataModel import BaseDataModel
from .enums.DatabaseEnums import DatabaseEnums
from .db_schemes import DataChunk
from sqlalchemy.future import select
from sqlalchemy import func, delete


class ChunkModel(BaseDataModel):

    def __init__(self, db_client):
        super().__init__(db_client)

    @classmethod
    async def get_instance(cls, db_client: object):
        instance = cls(db_client=db_client)  # cls == ProjectModel
        return instance

    async def insert_chunk(self, chunk: DataChunk):
        async with self.db_client() as session:
            async with session.begin():  # insert/update/delete
                session.add(chunk)
            await session.refresh(chunk)
        return chunk

    async def get_chunk(self, chunk_id: int):
        async with self.db_client() as session:
            query = select(DataChunk).where(DataChunk.chunk_id == chunk_id)
            result = await session.execute(query)
            chunk = result.scalar_one_or_none()
            if chunk is None:
                return None
        return chunk

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i : i + batch_size]
                    session.add_all(batch)
        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: int):
        async with self.db_client() as session:
            async with session.begin():
                query = delete(DataChunk).where(
                    DataChunk.chunk_project_id == project_id
                )
                result = await session.execute(query)
                delete_count = result.rowcount  # Get the number of deleted rows
        return delete_count

    async def get_chunks_by_project_id(
        self, chunk_project_id: int, page_no: int = 1, page_size: int = 50
    ):
        async with self.db_client() as session:
            query = (
                select(DataChunk)
                .where(DataChunk.chunk_project_id == chunk_project_id)
                .offset((page_no - 1) * page_size)
                .limit(page_size)
            )
            results = await session.execute(query)
            chunks = results.scalars().all()
        return chunks

    async def get_total_chunks_count(self, project_id: int):
        async with self.db_client() as session:
            query = select(func.count(DataChunk.chunk_id)).where(
                DataChunk.chunk_project_id == project_id
            )
            result = await session.execute(query)
            total_count = result.scalar_one()
        return total_count
