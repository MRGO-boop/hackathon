"""Centralized error handling module for CoreInventory.

This module provides a unified error handling system with standardized error classes
for different error categories and a consistent error response format.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCategory(Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_RULE = "business_rule"
    DATA = "data"


class CoreInventoryError(Exception):
    """Base exception for all CoreInventory errors.
    
    All errors include:
    - Error code (for programmatic handling)
    - Human-readable message
    - Context (entity ID, field name, etc.)
    - Timestamp
    - Category (for error classification)
    """
    
    def __init__(
        self,
        message: str,
        code: str,
        category: ErrorCategory,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize error with message, code, category, and context.
        
        Args:
            message: Human-readable error message
            code: Error code for programmatic handling
            category: Error category for classification
            context: Optional context dictionary with additional details
        """
        self.message = message
        self.code = code
        self.category = category
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for API responses.
        
        Returns:
            Dict containing error details in standardized format
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category.value,
                "context": self.context,
                "timestamp": self.timestamp
            }
        }


# Authentication Errors

class AuthenticationError(CoreInventoryError):
    """Base class for authentication-related errors."""
    
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, ErrorCategory.AUTHENTICATION, context)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            "Invalid email or password",
            "INVALID_CREDENTIALS",
            context
        )


class EmailAlreadyExistsError(AuthenticationError):
    """Raised when attempting to register with an existing email."""
    
    def __init__(self, email: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["email"] = email
        super().__init__(
            f"Email {email} is already registered",
            "EMAIL_EXISTS",
            ctx
        )


class InvalidOTPError(AuthenticationError):
    """Raised when OTP is invalid or expired."""
    
    def __init__(self, message: str = "Invalid or expired OTP", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_OTP", context)


class SessionExpiredError(AuthenticationError):
    """Raised when session has expired."""
    
    def __init__(self, session_id: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["session_id"] = session_id
        super().__init__(
            "Session has expired",
            "SESSION_EXPIRED",
            ctx
        )


class UnauthorizedAccessError(AuthenticationError):
    """Raised when user attempts unauthorized action."""
    
    def __init__(self, message: str = "Unauthorized access", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "UNAUTHORIZED_ACCESS", context)


# Validation Errors

class ValidationError(CoreInventoryError):
    """Base class for validation-related errors."""
    
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, ErrorCategory.VALIDATION, context)


class InsufficientStockError(ValidationError):
    """Raised when stock is insufficient for an operation."""
    
    def __init__(
        self,
        product_id: str,
        location_id: str,
        required: int,
        available: int,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        ctx.update({
            "product_id": product_id,
            "location_id": location_id,
            "required": required,
            "available": available
        })
        super().__init__(
            f"Insufficient stock: required {required}, available {available}",
            "INSUFFICIENT_STOCK",
            ctx
        )


class DuplicateSKUError(ValidationError):
    """Raised when attempting to create product with duplicate SKU."""
    
    def __init__(self, sku: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["sku"] = sku
        super().__init__(
            f"SKU {sku} already exists",
            "SKU_EXISTS",
            ctx
        )


class InvalidDocumentStatusError(ValidationError):
    """Raised when document status is invalid for operation."""
    
    def __init__(
        self,
        document_type: str,
        document_id: str,
        current_status: str,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        ctx.update({
            "document_type": document_type,
            "document_id": document_id,
            "current_status": current_status
        })
        super().__init__(
            f"Cannot perform operation on {document_type} with status {current_status}",
            "INVALID_STATUS",
            ctx
        )


class MissingRequiredFieldError(ValidationError):
    """Raised when required field is missing or empty."""
    
    def __init__(self, field_name: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["field"] = field_name
        super().__init__(
            f"{field_name} is required",
            "MISSING_REQUIRED_FIELD",
            ctx
        )


class InvalidQuantityError(ValidationError):
    """Raised when quantity is invalid (negative, zero where positive required, etc.)."""
    
    def __init__(self, message: str, quantity: Any, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["quantity"] = quantity
        super().__init__(message, "INVALID_QUANTITY", ctx)


class InvalidEmailFormatError(ValidationError):
    """Raised when email format is invalid."""
    
    def __init__(self, email: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["email"] = email
        super().__init__(
            f"Invalid email format: {email}",
            "INVALID_EMAIL_FORMAT",
            ctx
        )


# Business Rule Errors

class BusinessRuleError(CoreInventoryError):
    """Base class for business rule violation errors."""
    
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, ErrorCategory.BUSINESS_RULE, context)


class CannotModifyValidatedDocumentError(BusinessRuleError):
    """Raised when attempting to modify a validated document."""
    
    def __init__(
        self,
        document_type: str,
        document_id: str,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        ctx.update({
            "document_type": document_type,
            "document_id": document_id
        })
        super().__init__(
            f"Cannot modify validated {document_type}",
            "CANNOT_MODIFY_VALIDATED_DOCUMENT",
            ctx
        )


class CannotDeleteLocationWithStockError(BusinessRuleError):
    """Raised when attempting to delete location with existing stock."""
    
    def __init__(
        self,
        location_id: str,
        stock_count: int,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        ctx.update({
            "location_id": location_id,
            "stock_count": stock_count
        })
        super().__init__(
            f"Cannot delete location with existing stock. Location has {stock_count} product(s) with stock.",
            "LOCATION_HAS_STOCK",
            ctx
        )


class CannotTransferToSameLocationError(BusinessRuleError):
    """Raised when attempting to transfer to the same location."""
    
    def __init__(self, location_id: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["location_id"] = location_id
        super().__init__(
            "Source and destination locations must be different",
            "SAME_LOCATION",
            ctx
        )


class InvalidLocationHierarchyError(BusinessRuleError):
    """Raised when location hierarchy is invalid."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "INVALID_LOCATION_HIERARCHY", context)


# Data Errors

class DataError(CoreInventoryError):
    """Base class for data-related errors."""
    
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, ErrorCategory.DATA, context)


class EntityNotFoundError(DataError):
    """Raised when entity is not found in database."""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        ctx.update({
            "entity_type": entity_type,
            "entity_id": entity_id
        })
        super().__init__(
            f"{entity_type} not found",
            f"{entity_type.upper()}_NOT_FOUND",
            ctx
        )


class ForeignKeyConstraintError(DataError):
    """Raised when foreign key constraint is violated."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FOREIGN_KEY_CONSTRAINT", context)


class UniqueConstraintError(DataError):
    """Raised when unique constraint is violated."""
    
    def __init__(self, message: str, field: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx["field"] = field
        super().__init__(message, "UNIQUE_CONSTRAINT", ctx)


class InvalidIDFormatError(DataError):
    """Raised when ID format is invalid (not a valid UUID)."""
    
    def __init__(self, id_type: str, id_value: str, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        ctx.update({
            "id_type": id_type,
            "id_value": id_value
        })
        super().__init__(
            f"Invalid {id_type} format",
            "INVALID_ID_FORMAT",
            ctx
        )


class DatabaseError(DataError):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", context)
