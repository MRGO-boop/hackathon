# Error Handling and Validation Guide

## Overview

CoreInventory uses a centralized error handling system with standardized error classes and validation utilities. This guide explains how to use the error handling and validation modules.

## Error Categories

All errors are categorized into four main types:

1. **Authentication Errors** - User authentication and authorization issues
2. **Validation Errors** - Input validation failures
3. **Business Rule Errors** - Business logic violations
4. **Data Errors** - Database and data integrity issues

## Using Error Classes

### Import Error Classes

```python
from core_inventory.errors import (
    InvalidCredentialsError,
    InsufficientStockError,
    CannotModifyValidatedDocumentError,
    EntityNotFoundError
)
```

### Raising Errors

```python
# Authentication error
if not user:
    raise InvalidCredentialsError()

# Validation error with context
if stock < required:
    raise InsufficientStockError(
        product_id=product_id,
        location_id=location_id,
        required=required,
        available=stock
    )

# Business rule error
if document.status == "validated":
    raise CannotModifyValidatedDocumentError(
        document_type="receipt",
        document_id=str(document.id)
    )

# Data error
if not product:
    raise EntityNotFoundError(
        entity_type="Product",
        entity_id=product_id
    )
```

### Error Response Format

All errors provide a standardized response format:

```python
try:
    # Some operation
    pass
except CoreInventoryError as e:
    error_response = e.to_dict()
    # Returns:
    # {
    #     "error": {
    #         "code": "INSUFFICIENT_STOCK",
    #         "message": "Insufficient stock: required 100, available 50",
    #         "category": "validation",
    #         "context": {
    #             "product_id": "...",
    #             "location_id": "...",
    #             "required": 100,
    #             "available": 50
    #         },
    #         "timestamp": "2024-01-15T10:30:00Z"
    #     }
    # }
```

## Using Validation Utilities

### Import Validation Functions

```python
from core_inventory.validation import (
    validate_email,
    validate_required_string,
    validate_positive_integer,
    validate_uuid,
    validate_password
)
```

### Email Validation

```python
# Validates format and normalizes (lowercase, stripped)
email = validate_email(user_input_email)
# Returns: "user@example.com"
# Raises: MissingRequiredFieldError or InvalidEmailFormatError
```

### Required String Validation

```python
# Validates non-empty and strips whitespace
name = validate_required_string(user_input_name, "name")
# Returns: "John Doe"
# Raises: MissingRequiredFieldError if empty
```

### Positive Integer Validation

```python
# Validates positive integer (> 0)
quantity = validate_positive_integer(user_input_qty, "quantity")
# Returns: 100
# Raises: InvalidQuantityError if not positive integer

# Allow zero
quantity = validate_positive_integer(user_input_qty, "quantity", allow_zero=True)
# Returns: 0 or positive integer
```

### UUID Validation

```python
# Validates UUID format and returns UUID object
product_uuid = validate_uuid(product_id, "product_id")
# Returns: UUID object
# Raises: InvalidIDFormatError if invalid
```

### Password Validation

```python
# Validates minimum length (default: 8 characters)
password = validate_password(user_input_password)
# Returns: validated password
# Raises: MissingRequiredFieldError or InvalidQuantityError

# Custom minimum length
password = validate_password(user_input_password, min_length=12)
```

### Optional String Validation

```python
# Returns None if empty, otherwise stripped string
contact = validate_optional_string(user_input_contact)
# Returns: "123-456-7890" or None
```

### List Validation

```python
from core_inventory.validation import validate_list_not_empty

# Validates list is not empty
items = validate_list_not_empty(user_input_items, "items")
# Returns: list
# Raises: MissingRequiredFieldError if empty
```

### Different Values Validation

```python
from core_inventory.validation import validate_different_values

# Validates two values are different
validate_different_values(
    source_location_id,
    dest_location_id,
    "source_location",
    "destination_location"
)
# Raises: InvalidQuantityError if same
```

## Example: Complete Function with Validation

```python
from core_inventory.validation import (
    validate_required_string,
    validate_positive_integer,
    validate_uuid,
    validate_list_not_empty
)
from core_inventory.errors import (
    InsufficientStockError,
    EntityNotFoundError
)

def create_delivery_order(
    customer_name: str,
    created_by: str,
    items: List[Dict[str, Any]]
):
    """Create delivery order with proper validation."""
    
    # Validate inputs
    customer_name = validate_required_string(customer_name, "customer_name")
    created_by_uuid = validate_uuid(created_by, "created_by")
    items = validate_list_not_empty(items, "items")
    
    # Validate each item
    for item in items:
        product_uuid = validate_uuid(item['product_id'], "product_id")
        location_uuid = validate_uuid(item['location_id'], "location_id")
        quantity = validate_positive_integer(item['quantity'], "quantity")
        
        # Check stock availability
        available = get_stock(str(product_uuid), str(location_uuid))
        if available < quantity:
            raise InsufficientStockError(
                product_id=str(product_uuid),
                location_id=str(location_uuid),
                required=quantity,
                available=available
            )
    
    # Create delivery order...
```

## Migration from Old Error Classes

The existing component-specific error classes (AuthenticationError, ProductError, etc.) can be gradually migrated to use the new centralized error classes:

### Before (Old Pattern)

```python
class ProductError(Exception):
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)

# Usage
raise ProductError("SKU already exists", "SKU_EXISTS", {"sku": sku})
```

### After (New Pattern)

```python
from core_inventory.errors import DuplicateSKUError

# Usage
raise DuplicateSKUError(sku)
```

## Best Practices

1. **Use specific error classes** - Use the most specific error class available (e.g., `DuplicateSKUError` instead of generic `ValidationError`)

2. **Validate early** - Validate all inputs at the beginning of functions before performing operations

3. **Provide context** - Include relevant context in errors to help with debugging

4. **Use validation utilities** - Use the validation utilities instead of manual validation to ensure consistency

5. **Handle errors appropriately** - Catch specific error types and handle them appropriately in your application layer

6. **Log errors** - Log errors with full context for debugging and monitoring

## Error Codes Reference

### Authentication Errors
- `INVALID_CREDENTIALS` - Invalid email or password
- `EMAIL_EXISTS` - Email already registered
- `INVALID_OTP` - Invalid or expired OTP
- `SESSION_EXPIRED` - Session has expired
- `UNAUTHORIZED_ACCESS` - Unauthorized access attempt

### Validation Errors
- `INSUFFICIENT_STOCK` - Insufficient stock for operation
- `SKU_EXISTS` - Duplicate SKU
- `INVALID_STATUS` - Invalid document status
- `MISSING_REQUIRED_FIELD` - Required field missing
- `INVALID_QUANTITY` - Invalid quantity value
- `INVALID_EMAIL_FORMAT` - Invalid email format

### Business Rule Errors
- `CANNOT_MODIFY_VALIDATED_DOCUMENT` - Cannot modify validated document
- `LOCATION_HAS_STOCK` - Cannot delete location with stock
- `SAME_LOCATION` - Cannot transfer to same location
- `INVALID_LOCATION_HIERARCHY` - Invalid location hierarchy

### Data Errors
- `{ENTITY}_NOT_FOUND` - Entity not found (e.g., PRODUCT_NOT_FOUND)
- `FOREIGN_KEY_CONSTRAINT` - Foreign key constraint violation
- `UNIQUE_CONSTRAINT` - Unique constraint violation
- `INVALID_ID_FORMAT` - Invalid ID format
- `DATABASE_ERROR` - Database operation error
