from enum import Enum


class ResponseSignal(Enum):

    FILE_TYPE_NOT_SUPPORTED = "file type not supported"
    FILE_SIZE_EXCEEDED = "file size exceeded"
    FILE_UPLOAD_SUCCESS = "file upload success"
    FILE_UPLOAD_FILED = "file upload failed"
    PROCESSING_FAILED = "processing_failed"
    PROCESSING_SUCCESS = "processing_success"
    NO_FILES_ERROR = "not_files_found"
    FILE_ID_ERROR = "no_file_found_with_id"
    PROJECT_NOT_FOUND_ERROR = "project_not_found"
    INSERT_INTO_VECTOR_DB_ERROR = "insert_into_vector_db_failed"
    INSERT_INTO_VECTOR_DB_SUCCESS = "insert_into_vector_db_success"
    VECTOR_DB_COLLECTION_INFO = "vector_db_collection_info"
    VECTOR_DB_COLLECTION_INFO_NOT_FOUND = "vector_db_collection_not_found"
    VECTOR_DB_SEARCH_COLLECTION_ERROR = "vector_db_search_collection_failed"
    VECTOR_DB_SEARCH_COLLECTION_SUCCESS = "vector_db_search_collection_success"
    RAG_ANSWER_ERROR = "rag_answer_error"
    RAG_ANSWER_SUCCESS = "rag_answer_success"
