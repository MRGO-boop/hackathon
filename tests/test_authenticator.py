"""Unit tests for Authenticator component."""
import pytest
from datetime import datetime, timedelta
from core_inventory.components.authenticator import Authenticator, AuthenticationError
from core_inventory.models.user import User
from core_inventory.models.session import Session
from core_inventory.models.password_reset import PasswordReset


class TestSignup:
    """Tests for signup functionality."""
    
    def test_successful_signup(self, db_session):
        """Test successful user signup with valid credentials."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.password_hash is not None
        assert user.password_hash != "password123"  # Password should be hashed
        assert user.id is not None
    
    def test_signup_normalizes_email(self, db_session):
        """Test that signup normalizes email to lowercase."""
        auth = Authenticator(db_session)
        
        user = auth.signup("Test@Example.COM", "password123", "Test User")
        
        assert user.email == "test@example.com"
    
    def test_signup_duplicate_email_fails(self, db_session):
        """Test that signup fails when email already exists."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.signup("test@example.com", "password456", "Another User")
        
        assert exc_info.value.code == "EMAIL_EXISTS"
        assert "already registered" in exc_info.value.message.lower()
    
    def test_signup_empty_email_fails(self, db_session):
        """Test that signup fails with empty email."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.signup("", "password123", "Test User")
        
        assert exc_info.value.code == "INVALID_EMAIL"
    
    def test_signup_short_password_fails(self, db_session):
        """Test that signup fails with password less than 8 characters."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.signup("test@example.com", "short", "Test User")
        
        assert exc_info.value.code == "INVALID_PASSWORD"
        assert "8 characters" in exc_info.value.message
    
    def test_signup_empty_name_fails(self, db_session):
        """Test that signup fails with empty name."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.signup("test@example.com", "password123", "")
        
        assert exc_info.value.code == "INVALID_NAME"


class TestLogin:
    """Tests for login functionality."""
    
    def test_successful_login(self, db_session):
        """Test successful login with valid credentials."""
        auth = Authenticator(db_session)
        
        # Create user
        auth.signup("test@example.com", "password123", "Test User")
        
        # Login
        session = auth.login("test@example.com", "password123")
        
        assert session.id is not None
        assert session.user_id is not None
        assert session.expires_at > datetime.utcnow()
    
    def test_login_case_insensitive_email(self, db_session):
        """Test that login works with different email case."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        
        session = auth.login("Test@Example.COM", "password123")
        
        assert session.id is not None
    
    def test_login_wrong_password_fails(self, db_session):
        """Test that login fails with wrong password."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login("test@example.com", "wrongpassword")
        
        assert exc_info.value.code == "INVALID_CREDENTIALS"
    
    def test_login_nonexistent_email_fails(self, db_session):
        """Test that login fails with non-existent email."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login("nonexistent@example.com", "password123")
        
        assert exc_info.value.code == "INVALID_CREDENTIALS"
    
    def test_login_empty_email_fails(self, db_session):
        """Test that login fails with empty email."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login("", "password123")
        
        assert exc_info.value.code == "INVALID_CREDENTIALS"
    
    def test_login_empty_password_fails(self, db_session):
        """Test that login fails with empty password."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login("test@example.com", "")
        
        assert exc_info.value.code == "INVALID_CREDENTIALS"


class TestValidateSession:
    """Tests for session validation."""
    
    def test_validate_valid_session(self, db_session):
        """Test validating a valid session returns the user."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        session = auth.login("test@example.com", "password123")
        
        validated_user = auth.validate_session(str(session.id))
        
        assert validated_user.id == user.id
        assert validated_user.email == user.email
    
    def test_validate_expired_session_fails(self, db_session):
        """Test that validating an expired session fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        session = auth.login("test@example.com", "password123")
        
        # Manually expire the session
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.validate_session(str(session.id))
        
        assert exc_info.value.code == "SESSION_EXPIRED"
    
    def test_validate_nonexistent_session_fails(self, db_session):
        """Test that validating a non-existent session fails."""
        auth = Authenticator(db_session)
        
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.validate_session(fake_session_id)
        
        assert exc_info.value.code == "SESSION_NOT_FOUND"
    
    def test_validate_invalid_session_id_format_fails(self, db_session):
        """Test that validating an invalid session ID format fails."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.validate_session("not-a-uuid")
        
        assert exc_info.value.code == "INVALID_SESSION"
    
    def test_validate_empty_session_id_fails(self, db_session):
        """Test that validating an empty session ID fails."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.validate_session("")
        
        assert exc_info.value.code == "INVALID_SESSION"


class TestPasswordReset:
    """Tests for password reset functionality."""
    
    def test_request_password_reset_generates_otp(self, db_session):
        """Test that requesting password reset generates an OTP."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        
        otp = auth.request_password_reset("test@example.com")
        
        assert otp is not None
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_request_password_reset_nonexistent_email_fails(self, db_session):
        """Test that requesting password reset for non-existent email fails."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.request_password_reset("nonexistent@example.com")
        
        assert exc_info.value.code == "USER_NOT_FOUND"
    
    def test_reset_password_with_valid_otp(self, db_session):
        """Test resetting password with valid OTP."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        otp = auth.request_password_reset("test@example.com")
        
        auth.reset_password(otp, "newpassword123")
        
        # Verify can login with new password
        session = auth.login("test@example.com", "newpassword123")
        assert session.id is not None
    
    def test_reset_password_old_password_no_longer_works(self, db_session):
        """Test that old password no longer works after reset."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        otp = auth.request_password_reset("test@example.com")
        auth.reset_password(otp, "newpassword123")
        
        with pytest.raises(AuthenticationError):
            auth.login("test@example.com", "password123")
    
    def test_reset_password_invalid_otp_fails(self, db_session):
        """Test that resetting password with invalid OTP fails."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.reset_password("123456", "newpassword123")
        
        assert exc_info.value.code == "INVALID_OTP"
    
    def test_reset_password_otp_can_only_be_used_once(self, db_session):
        """Test that OTP can only be used once."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        otp = auth.request_password_reset("test@example.com")
        
        auth.reset_password(otp, "newpassword123")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.reset_password(otp, "anotherpassword123")
        
        assert exc_info.value.code == "INVALID_OTP"
    
    def test_reset_password_expired_otp_fails(self, db_session):
        """Test that expired OTP fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        otp = auth.request_password_reset("test@example.com")
        
        # Manually expire the OTP
        password_reset = db_session.query(PasswordReset).filter(
            PasswordReset.otp == otp
        ).first()
        password_reset.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db_session.commit()
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.reset_password(otp, "newpassword123")
        
        assert exc_info.value.code == "OTP_EXPIRED"
    
    def test_reset_password_short_password_fails(self, db_session):
        """Test that resetting with short password fails."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        otp = auth.request_password_reset("test@example.com")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.reset_password(otp, "short")
        
        assert exc_info.value.code == "INVALID_PASSWORD"


class TestLogout:
    """Tests for logout functionality."""
    
    def test_successful_logout(self, db_session):
        """Test successful logout removes session."""
        auth = Authenticator(db_session)
        
        auth.signup("test@example.com", "password123", "Test User")
        session = auth.login("test@example.com", "password123")
        
        auth.logout(str(session.id))
        
        # Verify session is deleted
        with pytest.raises(AuthenticationError) as exc_info:
            auth.validate_session(str(session.id))
        
        assert exc_info.value.code == "SESSION_NOT_FOUND"
    
    def test_logout_nonexistent_session_fails(self, db_session):
        """Test that logging out non-existent session fails."""
        auth = Authenticator(db_session)
        
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.logout(fake_session_id)
        
        assert exc_info.value.code == "SESSION_NOT_FOUND"
    
    def test_logout_invalid_session_id_format_fails(self, db_session):
        """Test that logging out with invalid session ID format fails."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.logout("not-a-uuid")
        
        assert exc_info.value.code == "INVALID_SESSION"


class TestGetProfile:
    """Tests for get profile functionality."""
    
    def test_get_profile_success(self, db_session):
        """Test getting user profile information."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        
        profile = auth.get_profile(str(user.id))
        
        assert profile["id"] == str(user.id)
        assert profile["name"] == "Test User"
        assert profile["email"] == "test@example.com"
    
    def test_get_profile_nonexistent_user_fails(self, db_session):
        """Test that getting profile for non-existent user fails."""
        auth = Authenticator(db_session)
        
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.get_profile(fake_user_id)
        
        assert exc_info.value.code == "USER_NOT_FOUND"
    
    def test_get_profile_invalid_user_id_format_fails(self, db_session):
        """Test that getting profile with invalid user ID format fails."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.get_profile("not-a-uuid")
        
        assert exc_info.value.code == "INVALID_USER_ID"
    
    def test_get_profile_empty_user_id_fails(self, db_session):
        """Test that getting profile with empty user ID fails."""
        auth = Authenticator(db_session)
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.get_profile("")
        
        assert exc_info.value.code == "INVALID_USER_ID"


class TestUpdateProfile:
    """Tests for update profile functionality."""
    
    def test_update_profile_name_only(self, db_session):
        """Test updating only the user's name."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Old Name")
        
        updated_user = auth.update_profile(str(user.id), name="New Name")
        
        assert updated_user.name == "New Name"
        assert updated_user.email == "test@example.com"
    
    def test_update_profile_email_only(self, db_session):
        """Test updating only the user's email."""
        auth = Authenticator(db_session)
        
        user = auth.signup("old@example.com", "password123", "Test User")
        
        updated_user = auth.update_profile(str(user.id), email="new@example.com")
        
        assert updated_user.name == "Test User"
        assert updated_user.email == "new@example.com"
    
    def test_update_profile_both_name_and_email(self, db_session):
        """Test updating both name and email."""
        auth = Authenticator(db_session)
        
        user = auth.signup("old@example.com", "password123", "Old Name")
        
        updated_user = auth.update_profile(str(user.id), name="New Name", email="new@example.com")
        
        assert updated_user.name == "New Name"
        assert updated_user.email == "new@example.com"
    
    def test_update_profile_normalizes_email(self, db_session):
        """Test that update profile normalizes email to lowercase."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        
        updated_user = auth.update_profile(str(user.id), email="New@Example.COM")
        
        assert updated_user.email == "new@example.com"
    
    def test_update_profile_duplicate_email_fails(self, db_session):
        """Test that updating to an existing email fails."""
        auth = Authenticator(db_session)
        
        user1 = auth.signup("user1@example.com", "password123", "User One")
        user2 = auth.signup("user2@example.com", "password456", "User Two")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.update_profile(str(user2.id), email="user1@example.com")
        
        assert exc_info.value.code == "EMAIL_EXISTS"
    
    def test_update_profile_empty_name_fails(self, db_session):
        """Test that updating to empty name fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.update_profile(str(user.id), name="")
        
        assert exc_info.value.code == "INVALID_NAME"
    
    def test_update_profile_empty_email_fails(self, db_session):
        """Test that updating to empty email fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.update_profile(str(user.id), email="")
        
        assert exc_info.value.code == "INVALID_EMAIL"
    
    def test_update_profile_nonexistent_user_fails(self, db_session):
        """Test that updating profile for non-existent user fails."""
        auth = Authenticator(db_session)
        
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.update_profile(fake_user_id, name="New Name")
        
        assert exc_info.value.code == "USER_NOT_FOUND"
    
    def test_update_profile_can_login_with_new_email(self, db_session):
        """Test that user can login with updated email."""
        auth = Authenticator(db_session)
        
        user = auth.signup("old@example.com", "password123", "Test User")
        auth.update_profile(str(user.id), email="new@example.com")
        
        # Should be able to login with new email
        session = auth.login("new@example.com", "password123")
        assert session.id is not None
        
        # Should not be able to login with old email
        with pytest.raises(AuthenticationError):
            auth.login("old@example.com", "password123")


class TestChangePassword:
    """Tests for change password functionality."""
    
    def test_change_password_success(self, db_session):
        """Test successfully changing password."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "oldpassword123", "Test User")
        
        auth.change_password(str(user.id), "oldpassword123", "newpassword123")
        
        # Should be able to login with new password
        session = auth.login("test@example.com", "newpassword123")
        assert session.id is not None
    
    def test_change_password_old_password_no_longer_works(self, db_session):
        """Test that old password no longer works after change."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "oldpassword123", "Test User")
        auth.change_password(str(user.id), "oldpassword123", "newpassword123")
        
        # Should not be able to login with old password
        with pytest.raises(AuthenticationError):
            auth.login("test@example.com", "oldpassword123")
    
    def test_change_password_wrong_current_password_fails(self, db_session):
        """Test that changing password with wrong current password fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "correctpassword123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.change_password(str(user.id), "wrongpassword", "newpassword123")
        
        assert exc_info.value.code == "INVALID_CREDENTIALS"
        assert "incorrect" in exc_info.value.message.lower()
    
    def test_change_password_short_new_password_fails(self, db_session):
        """Test that changing to short password fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "oldpassword123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.change_password(str(user.id), "oldpassword123", "short")
        
        assert exc_info.value.code == "INVALID_PASSWORD"
        assert "8 characters" in exc_info.value.message
    
    def test_change_password_empty_current_password_fails(self, db_session):
        """Test that changing password with empty current password fails."""
        auth = Authenticator(db_session)
        
        user = auth.signup("test@example.com", "password123", "Test User")
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.change_password(str(user.id), "", "newpassword123")
        
        assert exc_info.value.code == "INVALID_PASSWORD"
    
    def test_change_password_nonexistent_user_fails(self, db_session):
        """Test that changing password for non-existent user fails."""
        auth = Authenticator(db_session)
        
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.change_password(fake_user_id, "oldpassword123", "newpassword123")
        
        assert exc_info.value.code == "USER_NOT_FOUND"


class TestErrorHandling:
    """Tests for error handling and descriptive error messages."""
    
    def test_authentication_error_has_required_fields(self, db_session):
        """Test that AuthenticationError includes all required fields."""
        auth = Authenticator(db_session)
        
        try:
            auth.login("nonexistent@example.com", "password123")
        except AuthenticationError as e:
            assert e.message is not None
            assert e.code is not None
            assert e.timestamp is not None
            assert e.context is not None
            assert isinstance(e.context, dict)
    
    def test_error_messages_are_descriptive(self, db_session):
        """Test that error messages are descriptive and helpful."""
        auth = Authenticator(db_session)
        
        # Test various error scenarios
        with pytest.raises(AuthenticationError) as exc_info:
            auth.signup("test@example.com", "short", "Test User")
        assert "8 characters" in exc_info.value.message
        
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login("", "password123")
        assert "required" in exc_info.value.message.lower() or "invalid" in exc_info.value.message.lower()
