"""Input validation utilities for CoreInventory.

This module provides reusable validation functions for common input types
such as email format, positive quantities, non-empty required fields, etc.
"""
import re
import uuid
from typing import Any, Optional
from core_inventory.errors import (
    InvalidEmailFormatError,
    InvalidQuantityError,
    MissingRequiredFieldError,
    InvalidIDFormatError
)


# Email validation regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_email(email: str, field_name: str = "email") -> str:
    """Validate email format and return normalized email.
    
    Args:
        email: Email address to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        str: Normalized email (lowercase, stripped)
        
    Raises:
        MissingRequiredFieldError: If email is empty
        InvalidEmailFormatError: If email format is invalid
    """
    if not email or not email.strip():
        raise MissingRequiredFieldError(field_name)
    
    normalized_email = email.strip().lower()
    
    if not EMAIL_PATTERN.match(normalized_email):
        raise InvalidEmailFormatError(normalized_email, {"field": field_name})
    
    return normalized_email


def validate_required_string(value: str, field_name: str) -> str:
    """Validate that a string field is non-empty and return stripped value.
    
    Args:
        value: String value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        str: Stripped string value
        
    Raises:
        MissingRequiredFieldError: If value is empty or whitespace-only
    """
    if not value or not value.strip():
        raise MissingRequiredFieldError(field_name)
    
    return value.strip()


def validate_positive_integer(
    value: Any,
    field_name: str,
    allow_zero: bool = False
) -> int:
    """Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        allow_zero: Whether to allow zero as a valid value
        
    Returns:
        int: The validated integer value
        
    Raises:
        InvalidQuantityError: If value is not a positive integer
    """
    if not isinstance(value, int):
        raise InvalidQuantityError(
            f"{field_name} must be an integer",
            value,
            {"field": field_name}
        )
    
    if allow_zero:
        if value < 0:
            raise InvalidQuantityError(
                f"{field_name} must be non-negative",
                value,
                {"field": field_name}
            )
    else:
        if value <= 0:
            raise InvalidQuantityError(
                f"{field_name} must be positive",
                value,
                {"field": field_name}
            )
    
    return value


def validate_non_negative_integer(value: Any, field_name: str) -> int:
    """Validate that a value is a non-negative integer (>= 0).
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        int: The validated integer value
        
    Raises:
        InvalidQuantityError: If value is not a non-negative integer
    """
    return validate_positive_integer(value, field_name, allow_zero=True)


def validate_uuid(value: str, id_type: str = "ID") -> uuid.UUID:
    """Validate that a string is a valid UUID and return UUID object.
    
    Args:
        value: String value to validate as UUID
        id_type: Type of ID (for error messages, e.g., "user_id", "product_id")
        
    Returns:
        uuid.UUID: The validated UUID object
        
    Raises:
        InvalidIDFormatError: If value is not a valid UUID
    """
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        raise InvalidIDFormatError(id_type, value)


def validate_password(password: str, min_length: int = 8) -> str:
    """Validate password meets minimum requirements.
    
    Args:
        password: Password to validate
        min_length: Minimum password length (default: 8)
        
    Returns:
        str: The validated password
        
    Raises:
        MissingRequiredFieldError: If password is empty
        InvalidQuantityError: If password is too short
    """
    if not password:
        raise MissingRequiredFieldError("password")
    
    if len(password) < min_length:
        raise InvalidQuantityError(
            f"Password must be at least {min_length} characters long",
            len(password),
            {"field": "password", "min_length": min_length}
        )
    
    return password


def validate_optional_string(value: Optional[str]) -> Optional[str]:
    """Validate and normalize an optional string field.
    
    Args:
        value: Optional string value
        
    Returns:
        Optional[str]: Stripped string or None if empty
    """
    if value is None:
        return None
    
    stripped = value.strip()
    return stripped if stripped else None


def validate_enum_value(value: str, enum_class: type, field_name: str) -> Any:
    """Validate that a string value is a valid enum member.
    
    Args:
        value: String value to validate
        enum_class: Enum class to validate against
        field_name: Name of the field (for error messages)
        
    Returns:
        Enum member corresponding to the value
        
    Raises:
        MissingRequiredFieldError: If value is empty
        InvalidQuantityError: If value is not a valid enum member
    """
    if not value or not value.strip():
        raise MissingRequiredFieldError(field_name)
    
    try:
        return enum_class[value.strip()]
    except KeyError:
        valid_values = [e.name for e in enum_class]
        raise InvalidQuantityError(
            f"Invalid {field_name}: {value}. Must be one of: {', '.join(valid_values)}",
            value,
            {"field": field_name, "valid_values": valid_values}
        )


def validate_list_not_empty(value: list, field_name: str) -> list:
    """Validate that a list is not empty.
    
    Args:
        value: List to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        list: The validated list
        
    Raises:
        MissingRequiredFieldError: If list is empty or None
    """
    if not value or len(value) == 0:
        raise MissingRequiredFieldError(field_name)
    
    return value


def validate_different_values(
    value1: Any,
    value2: Any,
    field1_name: str,
    field2_name: str,
    error_message: Optional[str] = None
) -> None:
    """Validate that two values are different.
    
    Args:
        value1: First value
        value2: Second value
        field1_name: Name of first field
        field2_name: Name of second field
        error_message: Optional custom error message
        
    Raises:
        InvalidQuantityError: If values are the same
    """
    if value1 == value2:
        message = error_message or f"{field1_name} and {field2_name} must be different"
        raise InvalidQuantityError(
            message,
            value1,
            {field1_name: value1, field2_name: value2}
        )
