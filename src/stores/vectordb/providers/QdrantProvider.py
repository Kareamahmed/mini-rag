from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMetricEnums
from qdrant_client import QdrantClient, models
from uuid import uuid4
from qdrant_client.models import PointStruct
import logging
from models.db_schemes import RetrievedDocument


class QdrantProvider(VectorDBInterface):

    def __init__(
        self,
        db_path: str,
        distance_metric: str = None,
        default_vector_size: int = 512,
        index_threshold: int = 100,
    ):

        self.db_path = db_path
        self.distance_metric = None
        self.client = None
        self.default_vector_size = default_vector_size

        if distance_metric == DistanceMetricEnums.DOT.value:
            self.distance_metric = models.Distance.DOT
        elif distance_metric == DistanceMetricEnums.COSINE.value:
            self.distance_metric = models.Distance.COSINE

        self.logger = logging.getLogger(__name__)

    async def connect(self):
        self.client = QdrantClient(path=self.db_path)

    async def disconnect(self):
        self.client = None

    async def is_collection_exists(self, collection_name):
        return self.client.collection_exists(collection_name=collection_name)

    async def delete_collection(self, collection_name):
        if await self.is_collection_exists(collection_name=collection_name):
            return self.client.delete_collection(
                collection_name=collection_name
            )  # return True or False

    async def get_collection_info(self, collection_name):
        try:
            return self.client.get_collection(collection_name=collection_name)
        except Exception as e:
            self.logger.error(
                f"Failed to get collection info about {collection_name}: {e}"
            )
            return None

    async def get_all_collections(self):
        return self.client.get_collections()

    async def create_collection(self, collection_name, embedding_size, do_reset=False):
        if do_reset:
            await self.delete_collection(collection_name=collection_name)
        if not await self.is_collection_exists(collection_name=collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_metric
                ),
            )
            return True
        return False

    async def insert_one(
        self, collection_name, text, vector, metadata=None, chunk_id=None
    ):
        if not await self.is_collection_exists(collection_name=collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=str(uuid4()),
                        vector=vector,
                        payload={"text": text, "metadata": metadata},
                    )
                ],
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to insert point: {e}")
            return False

    async def insert_many(
        self,
        collection_name,
        texts,
        vectors,
        metadata=None,
        chunk_ids=None,
        batch_size=50,
    ):
        if not await self.is_collection_exists(collection_name=collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        if len(texts) != len(vectors):
            self.logger.error("texts and vectors must have the same length.")
            return False

        try:
            metadata = metadata or [{}] * len(texts)

            for i in range(0, len(texts), batch_size):
                points = []
                batch_end = i + batch_size

                for text, vector, meta in zip(
                    texts[i:batch_end],
                    vectors[i:batch_end],
                    metadata[i:batch_end],
                ):
                    points.append(
                        PointStruct(
                            id=str(uuid4()),
                            vector=vector,
                            payload={"text": text, "metadata": meta},
                        )
                    )

                self.client.upload_points(
                    collection_name=collection_name,
                    points=points,
                )

            return True

        except Exception as e:
            self.logger.error(f"Failed to insert points: {e}")
            return False

    async def search_by_vector(self, collection_name, vector, limit):

        if not await self.is_collection_exists(collection_name=collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        results = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        ).points

        return [
            RetrievedDocument(text=result.payload["text"], score=result.score)
            for result in results
        ]
