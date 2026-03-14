"""Stock model."""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
import uuid
from core_inventory.database import Base
from core_inventory.models.types import GUID


class Stock(Base):
    """Stock model for product quantities at locations."""
    
    __tablename__ = "stock"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(GUID, ForeignKey("products.id"), nullable=False, index=True)
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_product_location"),
    )
