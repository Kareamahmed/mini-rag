from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid


class Asset(SQLAlchemyBase):

    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(UUID, default=uuid.uuid4, nullable=False, unique=True)

    asset_name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    asset_size = Column(Integer, nullable=False)
    asset_created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    asset_config = Column(JSONB, nullable=True)

    asset_project_id = Column(
        Integer, ForeignKey("projects.project_id"), nullable=False
    )

    project = relationship(
        "Project", back_populates="assets"
    )  # many assets in one project
    chunks = relationship("DataChunk", back_populates="asset")

    __table_args__ = (Index("ix_asset_project_id", asset_project_id),)


# JSON
# → textual JSON representation

# JSONB
# → decomposed binary representation
