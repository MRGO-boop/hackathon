"""Product model."""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
import uuid
from core_inventory.database import Base
from core_inventory.models.types import GUID


class Product(Base):
    """Product model for inventory items."""
    
    __tablename__ = "products"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    unit_of_measure = Column(String(50), nullable=False)
    low_stock_threshold = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
