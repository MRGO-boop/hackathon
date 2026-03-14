"""Stock ledger model."""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
from core_inventory.database import Base
from core_inventory.models.types import GUID
from core_inventory.models.move_history import DocumentType


class StockLedger(Base):
    """Stock ledger model for comprehensive movement log with running balance."""
    
    __tablename__ = "stock_ledger"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=False, index=True)
    quantity_change = Column(Integer, nullable=False)
    running_balance = Column(Integer, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_id = Column(String(255), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
