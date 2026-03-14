"""Delivery order models."""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import uuid
import enum
from core_inventory.database import Base
from core_inventory.models.types import GUID


class DeliveryOrderStatus(enum.Enum):
    """Delivery order status enumeration."""
    pending = "pending"
    picking = "picking"
    packing = "packing"
    validated = "validated"


class DeliveryOrder(Base):
    """Delivery order model for outgoing goods."""
    
    __tablename__ = "delivery_orders"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    customer_name = Column(String(255), nullable=False)
    customer_contact = Column(String(255), nullable=True)
    status = Column(Enum(DeliveryOrderStatus), nullable=False, default=DeliveryOrderStatus.pending)
    validated_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DeliveryOrderItem(Base):
    """Delivery order item model for products in a delivery order."""
    
    __tablename__ = "delivery_order_items"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    delivery_order_id = Column(GUID, ForeignKey("delivery_orders.id"), nullable=False, index=True)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False)
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=False)
    requested_quantity = Column(Integer, nullable=False)
    delivered_quantity = Column(Integer, nullable=False)
