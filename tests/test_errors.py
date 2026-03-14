"""Unit tests for error handling module."""
import pytest
from datetime import datetime
from core_inventory.errors import (
    CoreInventoryError,
    ErrorCategory,
    AuthenticationError,
    InvalidCredentialsError,
    EmailAlreadyExistsError,
    InvalidOTPError,
    SessionExpiredError,
    UnauthorizedAccessError,
    ValidationError,
    InsufficientStockError,
    DuplicateSKUError,
    InvalidDocumentStatusError,
    MissingRequiredFieldError,
    InvalidQuantityError,
    InvalidEmailFormatError,
    BusinessRuleError,
    CannotModifyValidatedDocumentError,
    CannotDeleteLocationWithStockError,
    CannotTransferToSameLocationError,
    InvalidLocationHierarchyError,
    DataError,
    EntityNotFoundError,
    ForeignKeyConstraintError,
    UniqueConstraintError,
    InvalidIDFormatError,
    DatabaseError
)


class TestCoreInventoryError:
    """Test base error class."""
    
    def test_error_initialization(self):
        """Test error is initialized with all required fields."""
        error = CoreInventoryError(
            "Test error",
            "TEST_ERROR",
            ErrorCategory.VALIDATION,
            {"field": "test"}
        )
        
        assert error.message == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.category == ErrorCategory.VALIDATION
        assert error.context == {"field": "test"}
        assert error.timestamp is not None
    
    def test_error_to_dict(self):
        """Test error conversion to dictionary format."""
        error = CoreInventoryError(
            "Test error",
            "TEST_ERROR",
            ErrorCategory.VALIDATION,
            {"field": "test"}
        )
        
        error_dict = error.to_dict()
        
        assert "error" in error_dict
        assert error_dict["error"]["code"] == "TEST_ERROR"
        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["category"] == "validation"
        assert error_dict["error"]["context"] == {"field": "test"}
        assert "timestamp" in error_dict["error"]
    
    def test_error_without_context(self):
        """Test error initialization without context."""
        error = CoreInventoryError(
            "Test error",
            "TEST_ERROR",
            ErrorCategory.VALIDATION
        )
        
        assert error.context == {}


class TestAuthenticationErrors:
    """Test authentication error classes."""
    
    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError."""
        error = InvalidCredentialsError()
        
        assert error.code == "INVALID_CREDENTIALS"
        assert error.category == ErrorCategory.AUTHENTICATION
        assert "Invalid email or password" in error.message
    
    def test_email_already_exists_error(self):
        """Test EmailAlreadyExistsError."""
        error = EmailAlreadyExistsError("test@example.com")
        
        assert error.code == "EMAIL_EXISTS"
        assert error.category == ErrorCategory.AUTHENTICATION
        assert "test@example.com" in error.message
        assert error.context["email"] == "test@example.com"
    
    def test_invalid_otp_error(self):
        """Test InvalidOTPError."""
        error = InvalidOTPError()
        
        assert error.code == "INVALID_OTP"
        assert error.category == ErrorCategory.AUTHENTICATION
    
    def test_session_expired_error(self):
        """Test SessionExpiredError."""
        session_id = "test-session-123"
        error = SessionExpiredError(session_id)
        
        assert error.code == "SESSION_EXPIRED"
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.context["session_id"] == session_id
    
    def test_unauthorized_access_error(self):
        """Test UnauthorizedAccessError."""
        error = UnauthorizedAccessError()
        
        assert error.code == "UNAUTHORIZED_ACCESS"
        assert error.category == ErrorCategory.AUTHENTICATION


class TestValidationErrors:
    """Test validation error classes."""
    
    def test_insufficient_stock_error(self):
        """Test InsufficientStockError."""
        error = InsufficientStockError(
            product_id="prod-123",
            location_id="loc-456",
            required=100,
            available=50
        )
        
        assert error.code == "INSUFFICIENT_STOCK"
        assert error.category == ErrorCategory.VALIDATION
        assert "100" in error.message
        assert "50" in error.message
        assert error.context["product_id"] == "prod-123"
        assert error.context["location_id"] == "loc-456"
        assert error.context["required"] == 100
        assert error.context["available"] == 50
    
    def test_duplicate_sku_error(self):
        """Test DuplicateSKUError."""
        error = DuplicateSKUError("SKU-123")
        
        assert error.code == "SKU_EXISTS"
        assert error.category == ErrorCategory.VALIDATION
        assert "SKU-123" in error.message
        assert error.context["sku"] == "SKU-123"
    
    def test_invalid_document_status_error(self):
        """Test InvalidDocumentStatusError."""
        error = InvalidDocumentStatusError(
            document_type="receipt",
            document_id="doc-123",
            current_status="validated"
        )
        
        assert error.code == "INVALID_STATUS"
        assert error.category == ErrorCategory.VALIDATION
        assert "receipt" in error.message
        assert "validated" in error.message
    
    def test_missing_required_field_error(self):
        """Test MissingRequiredFieldError."""
        error = MissingRequiredFieldError("email")
        
        assert error.code == "MISSING_REQUIRED_FIELD"
        assert error.category == ErrorCategory.VALIDATION
        assert "email" in error.message
        assert error.context["field"] == "email"
    
    def test_invalid_quantity_error(self):
        """Test InvalidQuantityError."""
        error = InvalidQuantityError("Quantity must be positive", -5)
        
        assert error.code == "INVALID_QUANTITY"
        assert error.category == ErrorCategory.VALIDATION
        assert error.context["quantity"] == -5
    
    def test_invalid_email_format_error(self):
        """Test InvalidEmailFormatError."""
        error = InvalidEmailFormatError("invalid-email")
        
        assert error.code == "INVALID_EMAIL_FORMAT"
        assert error.category == ErrorCategory.VALIDATION
        assert "invalid-email" in error.message


class TestBusinessRuleErrors:
    """Test business rule error classes."""
    
    def test_cannot_modify_validated_document_error(self):
        """Test CannotModifyValidatedDocumentError."""
        error = CannotModifyValidatedDocumentError("receipt", "doc-123")
        
        assert error.code == "CANNOT_MODIFY_VALIDATED_DOCUMENT"
        assert error.category == ErrorCategory.BUSINESS_RULE
        assert "receipt" in error.message
        assert error.context["document_type"] == "receipt"
        assert error.context["document_id"] == "doc-123"
    
    def test_cannot_delete_location_with_stock_error(self):
        """Test CannotDeleteLocationWithStockError."""
        error = CannotDeleteLocationWithStockError("loc-123", 5)
        
        assert error.code == "LOCATION_HAS_STOCK"
        assert error.category == ErrorCategory.BUSINESS_RULE
        assert "5" in error.message
        assert error.context["location_id"] == "loc-123"
        assert error.context["stock_count"] == 5
    
    def test_cannot_transfer_to_same_location_error(self):
        """Test CannotTransferToSameLocationError."""
        error = CannotTransferToSameLocationError("loc-123")
        
        assert error.code == "SAME_LOCATION"
        assert error.category == ErrorCategory.BUSINESS_RULE
        assert error.context["location_id"] == "loc-123"
    
    def test_invalid_location_hierarchy_error(self):
        """Test InvalidLocationHierarchyError."""
        error = InvalidLocationHierarchyError("Invalid parent location")
        
        assert error.code == "INVALID_LOCATION_HIERARCHY"
        assert error.category == ErrorCategory.BUSINESS_RULE


class TestDataErrors:
    """Test data error classes."""
    
    def test_entity_not_found_error(self):
        """Test EntityNotFoundError."""
        error = EntityNotFoundError("Product", "prod-123")
        
        assert error.code == "PRODUCT_NOT_FOUND"
        assert error.category == ErrorCategory.DATA
        assert "Product" in error.message
        assert error.context["entity_type"] == "Product"
        assert error.context["entity_id"] == "prod-123"
    
    def test_foreign_key_constraint_error(self):
        """Test ForeignKeyConstraintError."""
        error = ForeignKeyConstraintError("Foreign key violation")
        
        assert error.code == "FOREIGN_KEY_CONSTRAINT"
        assert error.category == ErrorCategory.DATA
    
    def test_unique_constraint_error(self):
        """Test UniqueConstraintError."""
        error = UniqueConstraintError("Duplicate value", "email")
        
        assert error.code == "UNIQUE_CONSTRAINT"
        assert error.category == ErrorCategory.DATA
        assert error.context["field"] == "email"
    
    def test_invalid_id_format_error(self):
        """Test InvalidIDFormatError."""
        error = InvalidIDFormatError("user_id", "invalid-uuid")
        
        assert error.code == "INVALID_ID_FORMAT"
        assert error.category == ErrorCategory.DATA
        assert error.context["id_type"] == "user_id"
        assert error.context["id_value"] == "invalid-uuid"
    
    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError("Database connection failed")
        
        assert error.code == "DATABASE_ERROR"
        assert error.category == ErrorCategory.DATA


class TestErrorResponseFormat:
    """Test error response format matches design specification."""
    
    def test_error_response_has_all_required_fields(self):
        """Test error response includes code, message, context, and timestamp."""
        error = InsufficientStockError(
            product_id="prod-123",
            location_id="loc-456",
            required=100,
            available=50
        )
        
        response = error.to_dict()
        
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "context" in response["error"]
        assert "timestamp" in response["error"]
        assert "category" in response["error"]
    
    def test_timestamp_format(self):
        """Test timestamp is in ISO format with Z suffix."""
        error = CoreInventoryError(
            "Test",
            "TEST",
            ErrorCategory.VALIDATION
        )
        
        assert error.timestamp.endswith("Z")
        # Verify it's a valid ISO format by parsing
        datetime.fromisoformat(error.timestamp.replace("Z", "+00:00"))
