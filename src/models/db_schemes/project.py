from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from bson import ObjectId


class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(min_length=1)

    @field_validator("project_id")  # execute before create the object .
    @classmethod
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError("project_id must me alphanumeric")
        return value

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def get_indexes():
        return [
            {"key": [("project_id", 1)], "name": "project_id_index_1", "unique": True}
        ]
