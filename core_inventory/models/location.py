"""Location model."""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum
from core_inventory.database import Base
from core_inventory.models.types import GUID


class LocationType(enum.Enum):
    """Location type enumeration."""
    warehouse = "warehouse"
    rack = "rack"
    floor_area = "floor_area"


class Location(Base):
    """Location model for storage areas."""
    
    __tablename__ = "locations"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(Enum(LocationType), nullable=False)
    parent_id = Column(GUID, ForeignKey("locations.id"), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
