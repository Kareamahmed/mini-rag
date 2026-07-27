from enum import Enum


class LLMEnums(Enum):
    GEMINI = "gemini"
    COHERE = "cohere"

class GoogleEnums(Enum):
    USER = "user_input"

class CoHereEnums(Enum):
    USER = "user"

    DOCUMENT = "search_document"
    QUERY = "search_query"

class DocumentTypeEnums(Enum):
    DOCUMENT = "document"
    QUERY = "query"
