"""Unit tests for validation utilities."""
import pytest
import uuid
from enum import Enum
from core_inventory.validation import (
    validate_email,
    validate_required_string,
    validate_positive_integer,
    validate_non_negative_integer,
    validate_uuid,
    validate_password,
    validate_optional_string,
    validate_enum_value,
    validate_list_not_empty,
    validate_different_values
)
from core_inventory.errors import (
    InvalidEmailFormatError,
    InvalidQuantityError,
    MissingRequiredFieldError,
    InvalidIDFormatError
)


class TestEmailValidation:
    """Test email validation."""
    
    def test_valid_email(self):
        """Test validation of valid email addresses."""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("user.name@domain.co.uk") == "user.name@domain.co.uk"
        assert validate_email("TEST@EXAMPLE.COM") == "test@example.com"  # Normalized to lowercase
    
    def test_email_normalization(self):
        """Test email is normalized (lowercase, stripped)."""
        assert validate_email("  Test@Example.COM  ") == "test@example.com"
    
    def test_empty_email(self):
        """Test empty email raises error."""
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            validate_email("")
        assert exc_info.value.context["field"] == "email"
    
    def test_invalid_email_format(self):
        """Test invalid email format raises error."""
        with pytest.raises(InvalidEmailFormatError):
            validate_email("invalid-email")
        
        with pytest.raises(InvalidEmailFormatError):
            validate_email("@example.com")
        
        with pytest.raises(InvalidEmailFormatError):
            validate_email("test@")


class TestRequiredStringValidation:
    """Test required string validation."""
    
    def test_valid_string(self):
        """Test validation of valid non-empty strings."""
        assert validate_required_string("test", "name") == "test"
        assert validate_required_string("  test  ", "name") == "test"  # Stripped
    
    def test_empty_string(self):
        """Test empty string raises error."""
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            validate_required_string("", "name")
        assert exc_info.value.context["field"] == "name"
    
    def test_whitespace_only_string(self):
        """Test whitespace-only string raises error."""
        with pytest.raises(MissingRequiredFieldError):
            validate_required_string("   ", "name")


class TestPositiveIntegerValidation:
    """Test positive integer validation."""
    
    def test_valid_positive_integer(self):
        """Test validation of positive integers."""
        assert validate_positive_integer(1, "quantity") == 1
        assert validate_positive_integer(100, "quantity") == 100
    
    def test_zero_not_allowed_by_default(self):
        """Test zero is not allowed by default."""
        with pytest.raises(InvalidQuantityError) as exc_info:
            validate_positive_integer(0, "quantity")
        assert "positive" in exc_info.value.message.lower()
    
    def test_zero_allowed_when_specified(self):
        """Test zero is allowed when allow_zero=True."""
        assert validate_positive_integer(0, "quantity", allow_zero=True) == 0
    
    def test_negative_integer(self):
        """Test negative integer raises error."""
        with pytest.raises(InvalidQuantityError):
            validate_positive_integer(-5, "quantity")
    
    def test_non_integer_value(self):
        """Test non-integer value raises error."""
        with pytest.raises(InvalidQuantityError):
            validate_positive_integer("10", "quantity")
        
        with pytest.raises(InvalidQuantityError):
            validate_positive_integer(10.5, "quantity")


class TestNonNegativeIntegerValidation:
    """Test non-negative integer validation."""
    
    def test_valid_non_negative_integer(self):
        """Test validation of non-negative integers."""
        assert validate_non_negative_integer(0, "quantity") == 0
        assert validate_non_negative_integer(100, "quantity") == 100
    
    def test_negative_integer(self):
        """Test negative integer raises error."""
        with pytest.raises(InvalidQuantityError):
            validate_non_negative_integer(-1, "quantity")


class TestUUIDValidation:
    """Test UUID validation."""
    
    def test_valid_uuid(self):
        """Test validation of valid UUID strings."""
        test_uuid = str(uuid.uuid4())
        result = validate_uuid(test_uuid, "user_id")
        assert isinstance(result, uuid.UUID)
        assert str(result) == test_uuid
    
    def test_invalid_uuid(self):
        """Test invalid UUID string raises error."""
        with pytest.raises(InvalidIDFormatError) as exc_info:
            validate_uuid("not-a-uuid", "user_id")
        assert exc_info.value.context["id_type"] == "user_id"
        assert exc_info.value.context["id_value"] == "not-a-uuid"


class TestPasswordValidation:
    """Test password validation."""
    
    def test_valid_password(self):
        """Test validation of valid passwords."""
        assert validate_password("password123") == "password123"
        assert validate_password("12345678") == "12345678"
    
    def test_password_too_short(self):
        """Test password shorter than minimum length raises error."""
        with pytest.raises(InvalidQuantityError) as exc_info:
            validate_password("short")
        assert "8" in exc_info.value.message
    
    def test_empty_password(self):
        """Test empty password raises error."""
        with pytest.raises(MissingRequiredFieldError):
            validate_password("")
    
    def test_custom_min_length(self):
        """Test custom minimum password length."""
        assert validate_password("12345", min_length=5) == "12345"
        
        with pytest.raises(InvalidQuantityError):
            validate_password("1234", min_length=5)


class TestOptionalStringValidation:
    """Test optional string validation."""
    
    def test_none_value(self):
        """Test None value returns None."""
        assert validate_optional_string(None) is None
    
    def test_valid_string(self):
        """Test valid string is stripped."""
        assert validate_optional_string("  test  ") == "test"
    
    def test_empty_string_returns_none(self):
        """Test empty string returns None."""
        assert validate_optional_string("") is None
        assert validate_optional_string("   ") is None


class TestEnumValidation:
    """Test enum value validation."""
    
    class TestEnum(Enum):
        VALUE1 = "value1"
        VALUE2 = "value2"
    
    def test_valid_enum_value(self):
        """Test validation of valid enum values."""
        result = validate_enum_value("VALUE1", self.TestEnum, "status")
        assert result == self.TestEnum.VALUE1
    
    def test_invalid_enum_value(self):
        """Test invalid enum value raises error."""
        with pytest.raises(InvalidQuantityError) as exc_info:
            validate_enum_value("INVALID", self.TestEnum, "status")
        assert "VALUE1" in exc_info.value.message
        assert "VALUE2" in exc_info.value.message
    
    def test_empty_enum_value(self):
        """Test empty enum value raises error."""
        with pytest.raises(MissingRequiredFieldError):
            validate_enum_value("", self.TestEnum, "status")


class TestListValidation:
    """Test list validation."""
    
    def test_valid_list(self):
        """Test validation of non-empty lists."""
        assert validate_list_not_empty([1, 2, 3], "items") == [1, 2, 3]
    
    def test_empty_list(self):
        """Test empty list raises error."""
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            validate_list_not_empty([], "items")
        assert exc_info.value.context["field"] == "items"
    
    def test_none_list(self):
        """Test None list raises error."""
        with pytest.raises(MissingRequiredFieldError):
            validate_list_not_empty(None, "items")


class TestDifferentValuesValidation:
    """Test different values validation."""
    
    def test_different_values(self):
        """Test validation passes when values are different."""
        validate_different_values("a", "b", "field1", "field2")  # Should not raise
    
    def test_same_values(self):
        """Test validation fails when values are the same."""
        with pytest.raises(InvalidQuantityError) as exc_info:
            validate_different_values("a", "a", "source", "destination")
        assert "source" in exc_info.value.message
        assert "destination" in exc_info.value.message
    
    def test_custom_error_message(self):
        """Test custom error message is used."""
        with pytest.raises(InvalidQuantityError) as exc_info:
            validate_different_values(
                "a", "a",
                "source", "destination",
                error_message="Custom error"
            )
        assert "Custom error" in exc_info.value.message
