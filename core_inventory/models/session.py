"""Session model for user authentication."""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid
from core_inventory.database import Base
from core_inventory.models.types import GUID


class Session(Base):
    """Session model for maintaining user authentication state."""
    
    __tablename__ = "sessions"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
