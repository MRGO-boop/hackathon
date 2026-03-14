"""Transfer model."""
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum
from core_inventory.database import Base
from core_inventory.models.types import GUID


class TransferStatus(enum.Enum):
    """Transfer status enumeration."""
    pending = "pending"
    validated = "validated"


class Transfer(Base):
    """Transfer model for moving stock between locations."""
    
    __tablename__ = "transfers"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_location_id = Column(GUID, ForeignKey("locations.id"), nullable=False)
    destination_location_id = Column(GUID, ForeignKey("locations.id"), nullable=False)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(TransferStatus), nullable=False, default=TransferStatus.pending)
    validated_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
