# Refactoring Example: Using New Error Handling and Validation

This document shows how to refactor existing components to use the new centralized error handling and validation utilities.

## Example: Product Manager Refactoring

### Before (Current Implementation)

```python
def create_product(
    self,
    sku: str,
    name: str,
    category: str,
    unit_of_measure: str,
    low_stock_threshold: Optional[int] = None
) -> Product:
    # Validate required fields
    if not sku or not sku.strip():
        raise ProductError(
            "SKU is required",
            "INVALID_SKU",
            {"field": "sku"}
        )
    
    if not name or not name.strip():
        raise ProductError(
            "Product name is required",
            "INVALID_NAME",
            {"field": "name"}
        )
    
    # Check if SKU already exists
    existing_product = self.db.query(Product).filter(
        Product.sku == sku.strip()
    ).first()
    
    if existing_product:
        raise ProductError(
            f"SKU {sku} already exists",
            "SKU_EXISTS",
            {"sku": sku}
        )
    
    # Create product
    product = Product(
        id=uuid.uuid4(),
        sku=sku.strip(),
        name=name.strip(),
        category=category.strip(),
        unit_of_measure=unit_of_measure.strip(),
        low_stock_threshold=low_stock_threshold
    )
    
    self.db.add(product)
    self.db.commit()
    self.db.refresh(product)
    
    return product
```

### After (Using New Utilities)

```python
from core_inventory.validation import validate_required_string
from core_inventory.errors import DuplicateSKUError

def create_product(
    self,
    sku: str,
    name: str,
    category: str,
    unit_of_measure: str,
    low_stock_threshold: Optional[int] = None
) -> Product:
    # Validate required fields using validation utilities
    sku = validate_required_string(sku, "sku")
    name = validate_required_string(name, "name")
    category = validate_required_string(category, "category")
    unit_of_measure = validate_required_string(unit_of_measure, "unit_of_measure")
    
    # Check if SKU already exists
    existing_product = self.db.query(Product).filter(
        Product.sku == sku
    ).first()
    
    if existing_product:
        raise DuplicateSKUError(sku)
    
    # Create product
    product = Product(
        id=uuid.uuid4(),
        sku=sku,
        name=name,
        category=category,
        unit_of_measure=unit_of_measure,
        low_stock_threshold=low_stock_threshold
    )
    
    self.db.add(product)
    self.db.commit()
    self.db.refresh(product)
    
    return product
```

### Benefits

1. **Less code** - Validation utilities handle common patterns
2. **Consistent validation** - All components use the same validation logic
3. **Better error messages** - Specific error classes provide clear, consistent messages
4. **Easier testing** - Validation logic is tested once in the utilities module
5. **Automatic normalization** - Validation utilities handle trimming, case normalization, etc.

## Example: Transfer Creation with Multiple Validations

### Before

```python
def create_transfer(
    self,
    source_location_id: str,
    destination_location_id: str,
    product_id: str,
    quantity: int,
    created_by: str
) -> Transfer:
    # Validate quantity
    if not isinstance(quantity, int) or quantity <= 0:
        raise DocumentError(
            "Quantity must be a positive integer",
            "INVALID_QUANTITY",
            {"quantity": quantity}
        )
    
    # Parse IDs
    try:
        source_uuid = uuid.UUID(source_location_id)
        dest_uuid = uuid.UUID(destination_location_id)
        product_uuid = uuid.UUID(product_id)
        created_by_uuid = uuid.UUID(created_by)
    except (ValueError, AttributeError):
        raise DocumentError(
            "Invalid ID format",
            "INVALID_ID",
            {
                "source_location_id": source_location_id,
                "destination_location_id": destination_location_id,
                "product_id": product_id,
                "created_by": created_by
            }
        )
    
    # Validate source and destination are different
    if source_location_id == destination_location_id:
        raise DocumentError(
            "Source and destination locations must be different",
            "SAME_LOCATION",
            {
                "source_location_id": source_location_id,
                "destination_location_id": destination_location_id
            }
        )
    
    # ... rest of function
```

### After

```python
from core_inventory.validation import (
    validate_positive_integer,
    validate_uuid,
    validate_different_values
)
from core_inventory.errors import CannotTransferToSameLocationError

def create_transfer(
    self,
    source_location_id: str,
    destination_location_id: str,
    product_id: str,
    quantity: int,
    created_by: str
) -> Transfer:
    # Validate inputs
    quantity = validate_positive_integer(quantity, "quantity")
    source_uuid = validate_uuid(source_location_id, "source_location_id")
    dest_uuid = validate_uuid(destination_location_id, "destination_location_id")
    product_uuid = validate_uuid(product_id, "product_id")
    created_by_uuid = validate_uuid(created_by, "created_by")
    
    # Validate source and destination are different
    if source_location_id == destination_location_id:
        raise CannotTransferToSameLocationError(source_location_id)
    
    # ... rest of function
```

## Example: Authentication with Email Validation

### Before

```python
def signup(self, email: str, password: str, name: str) -> User:
    # Validate input
    if not email or not email.strip():
        raise AuthenticationError(
            "Email is required",
            "INVALID_EMAIL",
            {"field": "email"}
        )
    
    if not password or len(password) < 8:
        raise AuthenticationError(
            "Password must be at least 8 characters long",
            "INVALID_PASSWORD",
            {"field": "password", "min_length": 8}
        )
    
    if not name or not name.strip():
        raise AuthenticationError(
            "Name is required",
            "INVALID_NAME",
            {"field": "name"}
        )
    
    # Check if email already exists
    existing_user = self.db.query(User).filter(
        User.email == email.strip().lower()
    ).first()
    
    if existing_user:
        raise AuthenticationError(
            f"Email {email} is already registered",
            "EMAIL_EXISTS",
            {"email": email}
        )
    
    # ... rest of function
```

### After

```python
from core_inventory.validation import (
    validate_email,
    validate_password,
    validate_required_string
)
from core_inventory.errors import EmailAlreadyExistsError

def signup(self, email: str, password: str, name: str) -> User:
    # Validate inputs
    email = validate_email(email)  # Automatically normalized
    password = validate_password(password)
    name = validate_required_string(name, "name")
    
    # Check if email already exists
    existing_user = self.db.query(User).filter(
        User.email == email
    ).first()
    
    if existing_user:
        raise EmailAlreadyExistsError(email)
    
    # ... rest of function
```

## Migration Strategy

### Phase 1: Add New Modules (Completed)
- ✅ Create `core_inventory/errors.py`
- ✅ Create `core_inventory/validation.py`
- ✅ Add comprehensive tests

### Phase 2: Update Components (Gradual)
1. Start with new features - use new error handling from the start
2. Refactor existing components one at a time
3. Keep old error classes for backward compatibility during transition
4. Update tests to use new error classes

### Phase 3: Deprecate Old Classes (Future)
1. Mark old error classes as deprecated
2. Update all components to use new classes
3. Remove old error classes in next major version

## Backward Compatibility

During the transition period, both old and new error classes can coexist:

```python
# Old code still works
try:
    product_manager.create_product(...)
except ProductError as e:
    # Handle old error
    pass

# New code uses new errors
try:
    product_manager.create_product(...)
except DuplicateSKUError as e:
    # Handle new error
    pass
```

## Testing Considerations

### Before

```python
def test_create_product_duplicate_sku():
    with pytest.raises(ProductError) as exc_info:
        product_manager.create_product(sku="DUPLICATE", ...)
    
    assert exc_info.value.code == "SKU_EXISTS"
```

### After

```python
def test_create_product_duplicate_sku():
    with pytest.raises(DuplicateSKUError) as exc_info:
        product_manager.create_product(sku="DUPLICATE", ...)
    
    assert exc_info.value.code == "SKU_EXISTS"
    assert exc_info.value.context["sku"] == "DUPLICATE"
```

## Summary

The new error handling and validation system provides:

1. **Centralized error definitions** - All error types in one place
2. **Reusable validation utilities** - Common validations available to all components
3. **Consistent error format** - All errors follow the same structure
4. **Better error messages** - Specific error classes with clear messages
5. **Easier maintenance** - Changes to error handling in one place
6. **Type safety** - Specific error classes make error handling more explicit
