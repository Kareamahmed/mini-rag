from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from bson import ObjectId
from datetime import datetime


class File(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    file_project_id: ObjectId
    file_name: str = Field(...)
    file_size: int = Field(default=None, gt=0)
    file_type: str
    file_pushed_at: datetime = Field(default=datetime.now())

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def get_indexes():
        return [
            {
                "key": [("file_project_id", 1)],
                "name": "file_project_id_index_1",
                "unique": False,
            },
            {
                "key": [("file_project_id", 1), ("file_name", 1)],
                "name": "file_project_id_name_index_1",
                "unique": True,
            },
        ]
