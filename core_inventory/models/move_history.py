"""Move history model."""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum
from core_inventory.database import Base
from core_inventory.models.types import GUID


class DocumentType(enum.Enum):
    """Document type enumeration for move history."""
    receipt = "receipt"
    delivery_order = "delivery_order"
    transfer = "transfer"
    stock_adjustment = "stock_adjustment"
    initial_stock = "initial_stock"


class MoveHistory(Base):
    """Move history model for tracking all stock movements."""
    
    __tablename__ = "move_history"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=False, index=True)
    quantity_change = Column(Integer, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False, index=True)
    document_id = Column(String(255), nullable=False)
    source_location_id = Column(GUID, ForeignKey("locations.id"), nullable=True)
    destination_location_id = Column(GUID, ForeignKey("locations.id"), nullable=True)
    reason = Column(String(500), nullable=True)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
