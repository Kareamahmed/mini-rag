from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMetricEnums
from qdrant_client import QdrantClient, models
from uuid import uuid4
from qdrant_client.models import PointStruct
import logging


class Qdrant(VectorDBInterface):

    def __init__(self, db_path: str, distance_metric: str):

        self.db_path = db_path
        self.distance_metric = None
        self.client = None

        if distance_metric == DistanceMetricEnums.DOT.value:
            self.distance_metric = models.Distance.DOT
        elif distance_metric == DistanceMetricEnums.COSINE.value:
            self.distance_metric = models.Distance.COSINE

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_exists(self, collection_name):
        return self.client.collection_exists(collection_name=collection_name)

    def delete_collection(self, collection_name):
        if self.is_collection_exists(collection_name=collection_name):
            return self.client.delete_collection(
                collection_name=collection_name
            )  # return True or False

    def get_collection_info(self, collection_name):
        return self.client.get_collection(collection_name=collection_name)

    def get_all_collections(self):
        return self.client.get_collections()

    def create_collection(self, collection_name, embedding_size, do_reset=False):
        if do_reset:
            self.delete_collection(collection_name=collection_name)
        if not self.is_collection_exists(collection_name=collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=self.distance_metric
                ),
            )
            return True
        return False

    def insert_one(self, collection_name, text, vector, metadata=None):
        if not self.is_collection_exists(collection_name=collection_name):
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

    def insert_many(
        self, collection_name, texts, vectors, metadata=None, batch_size=50
    ):
        if not self.is_collection_exists(collection_name=collection_name):
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

    def search_by_vector(self, collection_name, vector, limit):

        if not self.is_collection_exists(collection_name=collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        return self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        ).points
