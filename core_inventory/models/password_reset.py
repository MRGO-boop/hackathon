"""Password reset OTP model."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
import uuid
from core_inventory.database import Base
from core_inventory.models.types import GUID


class PasswordReset(Base):
    """Password reset OTP model for handling password reset requests."""
    
    __tablename__ = "password_resets"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    otp = Column(String(6), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
