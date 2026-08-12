from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import (
    DistanceMetricEnums,
    PgvectorDistanceMetricEnums,
    PgvectorIndexTypeEnums,
    PgvectorTableSchemaEnums,
)
import logging
from models.db_schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text


class PGVectorProvider(VectorDBInterface):

    def __init__(
        self,
        db_client,
        distance_metric: str = None,
        default_vector_size: int = 512,
        index_threshold: int = 100,
    ):

        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.table_prefix = PgvectorTableSchemaEnums._PREFIX.value
        self.index_threshold = index_threshold
        if distance_metric == DistanceMetricEnums.COSINE.value:
            self.distance_metric = PgvectorDistanceMetricEnums.COSINE.value
        else:
            self.distance_metric = PgvectorDistanceMetricEnums.L2.value

        self.logger = logging.getLogger("uvicorn")

        self.index_name = lambda collection_name: f"{collection_name}_vector_index"

    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))

    def disconnect(self):
        pass

    async def is_collection_exists(self, collection_name):
        async with self.db_client() as session:
            async with session.begin():
                sql = sql_text(
                    "SELECT * FROM pg_tables where tablename = :collection_name"
                )
                results = await session.execute(
                    sql, {"collection_name": collection_name}
                )
                row = results.scalar_one_or_none()
            return row

    async def get_collection_info(self, collection_name):
        async with self.db_client() as session:
            async with session.begin():
                table_info_sql = sql_text(
                    "SELECT * FROM pg_tables where tablename = :collection_name"
                )
                table_info_results = await session.execute(
                    table_info_sql, {"collection_name": collection_name}
                )
                table_info = table_info_results.mappings().one_or_none()

                if table_info is None:
                    return None

                safe_collection_name = collection_name.replace('"', '""')
                count_sql = sql_text(f'select count(*) from "{safe_collection_name}"')
                count_results = await session.execute(count_sql)
                count_rows = count_results.scalar_one_or_none()

            return {
                "table_info": table_info,
                "count_rows": count_rows,
            }

    async def get_all_collections(self):
        async with self.db_client() as session:
            async with session.begin():
                sql = sql_text(
                    "select tablename from pg_tables where tablename like :prefix"
                )
                results = await session.execute(sql, {"prefix": self.table_prefix})
                rows = results.scalars().all()
            return rows

    async def delete_collection(self, collection_name):
        if not self.is_collection_exists(collection_name=collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False
        async with self.db_client() as session:
            async with session.begin():
                safe_collection_name = collection_name.replace('"', '""')
                sql = sql_text(f'DROP TABLE IF EXISTS "{safe_collection_name}"')
                await session.execute(sql)
                self.logger.info(f"Collection {collection_name} deleted successfully.")
        return True

    async def create_collection(self, collection_name, embedding_size, do_reset=False):
        if do_reset:
            await self.delete_collection(collection_name=collection_name)

        is_table_existed = self.is_collection_exists(collection_name=collection_name)

        if not is_table_existed:
            async with self.db_client() as session:
                async with session.begin():
                    safe_collection_name = collection_name.replace('"', '""')
                    id_col = PgvectorTableSchemaEnums.ID.value
                    chunk_id_col = PgvectorTableSchemaEnums.CHUNK_ID.value
                    text_col = PgvectorTableSchemaEnums.TEXT.value
                    vector_col = PgvectorTableSchemaEnums.VECTOR.value
                    metadata_col = PgvectorTableSchemaEnums.METADATA.value

                    sql = sql_text(f"""
                        CREATE TABLE "{safe_collection_name}" (
                            {id_col} SERIAL PRIMARY KEY,
                            {chunk_id_col} INT,
                            {text_col} TEXT,
                            {vector_col} VECTOR({embedding_size}),
                            {metadata_col} JSONB,
                            foreign key ({chunk_id_col}) references chunks(chunk_id) on delete cascade
                        );
                        """)
                    await session.execute(sql)
            self.logger.info(f"Collection {collection_name} created successfully.")
            return True
        return False

    async def insert_one(
        self, collection_name, text, vector, metadata=None, chunk_id=None
    ):

        is_table_existed = self.is_collection_exists(collection_name=collection_name)
        if not is_table_existed:
            self.logger.error(
                f"cannot insert into collection {collection_name} because it does not exist."
            )
            return False
        if not chunk_id:
            self.logger.error(
                f"cannot insert into collection {collection_name} because chunk_id is not provided."
            )
            return False
        async with self.db_client() as session:
            async with session.begin():
                safe_collection_name = collection_name.replace('"', '""')
                id_col = PgvectorTableSchemaEnums.ID.value
                chunk_id_col = PgvectorTableSchemaEnums.CHUNK_ID.value
                text_col = PgvectorTableSchemaEnums.TEXT.value
                vector_col = PgvectorTableSchemaEnums.VECTOR.value
                metadata_col = PgvectorTableSchemaEnums.METADATA.value

                sql = sql_text(f"""
                    INSERT INTO "{safe_collection_name}" ({text_col}, {vector_col}, {metadata_col}, {chunk_id_col})
                    VALUES (:text, :vector, :metadata, :chunk_id)
                    RETURNING {id_col};
                    """)
                result = await session.execute(
                    sql,
                    {
                        "text": text,
                        "vector": "[" + ",".join([str(v) for v in vector]) + "]",
                        "metadata": metadata,
                        "chunk_id": chunk_id,
                    },
                )
                inserted_id = result.scalar_one()
        return inserted_id

    async def insert_many(
        self,
        collection_name,
        texts,
        vectors,
        metadata=None,
        chunk_ids=None,
        batch_size=50,
    ):
        is_table_existed = self.is_collection_exists(collection_name=collection_name)
        if not is_table_existed:
            self.logger.error(
                f"cannot insert into collection {collection_name} because it does not exist."
            )
            return False

        if len(texts) != len(vectors):
            self.logger.error("texts and vectors must have the same length.")
            return False

        metadata = metadata or [{}] * len(texts)

        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i : i + batch_size]
                    batch_vectors = vectors[i : i + batch_size]
                    batch_metadata = metadata[i : i + batch_size]
                    batch_chunk_ids = chunk_ids[i : i + batch_size]

                    safe_collection_name = collection_name.replace('"', '""')
                    text_col = PgvectorTableSchemaEnums.TEXT.value
                    vector_col = PgvectorTableSchemaEnums.VECTOR.value
                    metadata_col = PgvectorTableSchemaEnums.METADATA.value
                    chunk_id_col = PgvectorTableSchemaEnums.CHUNK_ID.value

                    values = []
                    for text, vector, meta, chunk_id in zip(
                        batch_texts, batch_vectors, batch_metadata, batch_chunk_ids
                    ):
                        values.append(
                            {
                                "text": text,
                                "vector": "["
                                + ",".join([str(v) for v in vector])
                                + "]",
                                "metadata": meta,
                                "chunk_id": chunk_id,
                            },
                        )
                    sql = sql_text(f"""
                        INSERT INTO "{safe_collection_name}" ({text_col}, {vector_col}, {metadata_col}, {chunk_id_col})
                        VALUES (:text, :vector, :metadata, :chunk_id);
                        """)
                    await session.execute(sql, values)
        return True

    async def search_by_vector(self, collection_name, vector, limit):
        is_table_existed = self.is_collection_exists(collection_name=collection_name)
        if not is_table_existed:
            self.logger.error(
                f"cannot search in collection {collection_name} because it does not exist."
            )
            return False

        async with self.db_client() as session:
            async with session.begin():
                safe_collection_name = collection_name.replace('"', '""')
                text_col = PgvectorTableSchemaEnums.TEXT.value
                vector_col = PgvectorTableSchemaEnums.VECTOR.value

                sql = sql_text(f"""
                    SELECT {text_col}, 1 - ({vector_col} <=> :vector) AS score   
                    FROM "{safe_collection_name}"
                    ORDER BY score DESC
                    LIMIT :limit;
                    """)
                result = await session.execute(
                    sql,
                    {
                        "vector": "[" + ",".join([str(v) for v in vector]) + "]",
                        "limit": limit,
                    },
                )
                rows = result.fetchall()

        if not rows or len(rows) == 0:
            return None
        return [RetrievedDocument(text=row[0], score=row[1]) for row in rows]

    async def is_index_exists(self, collection_name):
        index_name = self.index_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                sql = sql_text(
                    "SELECT 1 FROM pg_indexes where tablename = :collection_name and indexname = :index_name"
                )
                results = await session.execute(
                    sql, {"collection_name": collection_name, "index_name": index_name}
                )
                row = results.scalar_one_or_none()
            return bool(row)

    async def create_index(
        self, collection_name, index_type: str = PgvectorIndexTypeEnums.HNSW.value
    ):
        is_index_existed = await self.is_index_exists(collection_name=collection_name)
        if is_index_existed:
            self.logger.info(f"Index for collection {collection_name} already exists.")
            return False
        async with self.db_client() as session:
            async with session.begin():
                count_sql = sql_text(f'select count(*) from "{collection_name}"')
                count_results = await session.execute(count_sql)
                count_rows = count_results.scalar_one()

                if count_rows < self.index_threshold:
                    self.logger.info(
                        f"Collection {collection_name} has less than {self.index_threshold} rows. Skipping index creation."
                    )
                    return False

                self.logger.info(
                    f"Starting to create index for collection {collection_name} with index type {index_type}."
                )

                index_name = self.index_name(collection_name)
                safe_collection_name = collection_name.replace('"', '""')
                sql = sql_text(f"""
                    CREATE INDEX {index_name} ON "{safe_collection_name}" USING {index_type} ({PgvectorTableSchemaEnums.VECTOR.value} {self.distance_metric});
                    """)
                await session.execute(sql)

                self.logger.info(
                    f"Index {index_name} created successfully for collection {collection_name}."
                )
    async def reset_index(self, collection_name , index_type: str = PgvectorIndexTypeEnums.HNSW.value):

        async with self.db_client() as session:
            async with session.begin():
                index_name = self.index_name(collection_name)
                sql = sql_text(f'DROP INDEX IF EXISTS {index_name};')
                await session.execute(sql)
                self.logger.info(
                    f"Index {index_name} dropped successfully for collection {collection_name}."
                )
        return await self.create_index(collection_name=collection_name , index_type=index_type)

# pgvector
# cosine distance = 1 - cos(θ)
