from enum import Enum


class VectorDBEnums(Enum):
    QDRANT = 'qdrant'


class DistanceMetricEnums(Enum):
    COSINE = 'cosine'
    DOT = 'dot'