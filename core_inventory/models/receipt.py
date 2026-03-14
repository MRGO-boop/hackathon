"""Receipt models."""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum
from core_inventory.database import Base
from core_inventory.models.types import GUID


class ReceiptStatus(enum.Enum):
    """Receipt status enumeration."""
    pending = "pending"
    validated = "validated"


class Receipt(Base):
    """Receipt model for incoming goods."""
    
    __tablename__ = "receipts"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    supplier_name = Column(String(255), nullable=False)
    supplier_contact = Column(String(255), nullable=True)
    status = Column(Enum(ReceiptStatus), nullable=False, default=ReceiptStatus.pending)
    validated_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReceiptItem(Base):
    """Receipt item model for products in a receipt."""
    
    __tablename__ = "receipt_items"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    receipt_id = Column(GUID, ForeignKey("receipts.id"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False)
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=False)
    expected_quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, nullable=False)
