"""Stock adjustment model."""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum
from core_inventory.database import Base
from core_inventory.models.types import GUID


class StockAdjustmentStatus(enum.Enum):
    """Stock adjustment status enumeration."""
    pending = "pending"
    validated = "validated"


class StockAdjustment(Base):
    """Stock adjustment model for reconciling physical counts."""
    
    __tablename__ = "stock_adjustments"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False)
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=False)
    recorded_quantity = Column(Integer, nullable=False)
    physical_quantity = Column(Integer, nullable=False)
    adjustment_difference = Column(Integer, nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(Enum(StockAdjustmentStatus), nullable=False, default=StockAdjustmentStatus.pending)
    validated_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
