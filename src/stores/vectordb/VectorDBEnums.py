from enum import Enum


class VectorDBEnums(Enum):
    QDRANT = "qdrant"


class DistanceMetricEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"


class PgvectorTableSchemaEnums(Enum):
    ID = "id"
    Text = "text"
    VECTOR = "vector"
    METADATA = "metadata"
    _PREFIX = "pgvector"


class PgvectorDistanceMetricEnums(Enum):
    COSINE = "vector_cosine_ops"
    L2 = "vector_l2_ops"


class PgvectorIndexTypeEnums(Enum):
    IVFFLAT = "ivfflat"
    HNSW = "hnsw"
