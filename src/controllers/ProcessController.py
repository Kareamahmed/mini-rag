from pathlib import Path
from models import ProcessEnums
import os
from .ProjectController import ProjectController
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ProcessController:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader.load() # [ Document(page_content=.... , metadata = ....)]
        return None

    def get_file_chunks(
        self, file_content: list, chunk_size: int = 100, chunk_overlap: int = 30
    ):
        # Split text recursively by paragraphs, then lines, then words, and finally characters
        # to preserve semantic meaning while keeping chunks within the target size.

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        file_content_text = [rec.page_content for rec in file_content]
        file_content_metadata = [rec.metadata for rec in file_content]

        chunks = splitter.create_documents(
            texts=file_content_text, metadatas=file_content_metadata
        )

        return chunks

    def get_file_loader(self, file_id: str):

        file_ext = self.get_file_extension(file_id=file_id)

        file_path = os.path.join(self.project_path, file_id)

        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessEnums.TXT.value:
            return TextLoader(file_path=file_path, encoding="utf-8")

        if file_ext == ProcessEnums.PDF.value:
            return PyPDFLoader(file_path=file_path)

        return None

    def get_file_extension(self, file_id: str):
        return Path(file_id).suffix
