"""Integration tests for Authenticator component."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from core_inventory.components.authenticator import Authenticator, AuthenticationError


class TestAuthenticationFlow:
    """Integration tests for complete authentication workflows."""
    
    def test_complete_signup_login_logout_flow(self, db_session):
        """Test complete flow: signup -> login -> validate -> logout."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("test@example.com", "password123", "Test User")
        assert user.id is not None
        
        # Login
        session = auth.login("test@example.com", "password123")
        assert session.id is not None
        
        # Validate session
        validated_user = auth.validate_session(str(session.id))
        assert validated_user.id == user.id
        
        # Logout
        auth.logout(str(session.id))
        
        # Verify session is invalid after logout
        with pytest.raises(Exception):
            auth.validate_session(str(session.id))
    
    def test_complete_password_reset_flow(self, db_session):
        """Test complete flow: signup -> request reset -> reset -> login with new password."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("test@example.com", "oldpassword123", "Test User")
        
        # Request password reset
        otp = auth.request_password_reset("test@example.com")
        assert len(otp) == 6
        
        # Reset password
        auth.reset_password(otp, "newpassword123")
        
        # Login with new password
        session = auth.login("test@example.com", "newpassword123")
        assert session.id is not None
        
        # Verify old password doesn't work
        with pytest.raises(Exception):
            auth.login("test@example.com", "oldpassword123")
    
    def test_multiple_users_independent_sessions(self, db_session):
        """Test that multiple users can have independent sessions."""
        auth = Authenticator(db_session)
        
        # Create two users
        user1 = auth.signup("user1@example.com", "password123", "User One")
        user2 = auth.signup("user2@example.com", "password456", "User Two")
        
        # Login both users
        session1 = auth.login("user1@example.com", "password123")
        session2 = auth.login("user2@example.com", "password456")
        
        # Validate both sessions
        validated_user1 = auth.validate_session(str(session1.id))
        validated_user2 = auth.validate_session(str(session2.id))
        
        assert validated_user1.id == user1.id
        assert validated_user2.id == user2.id
        assert validated_user1.id != validated_user2.id
        
        # Logout user1
        auth.logout(str(session1.id))
        
        # User1 session should be invalid
        with pytest.raises(Exception):
            auth.validate_session(str(session1.id))
        
        # User2 session should still be valid
        validated_user2_again = auth.validate_session(str(session2.id))
        assert validated_user2_again.id == user2.id
    
    def test_multiple_login_sessions_for_same_user(self, db_session):
        """Test that a user can have multiple active sessions."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("test@example.com", "password123", "Test User")
        
        # Login multiple times
        session1 = auth.login("test@example.com", "password123")
        session2 = auth.login("test@example.com", "password123")
        
        # Both sessions should be valid
        validated_user1 = auth.validate_session(str(session1.id))
        validated_user2 = auth.validate_session(str(session2.id))
        
        assert validated_user1.id == user.id
        assert validated_user2.id == user.id
        assert session1.id != session2.id


class TestPropertyBasedAuthentication:
    """Property-based tests for authentication."""
    
    @given(
        email=st.one_of(
            st.text(min_size=1, max_size=100),  # Random text
            st.emails(),  # Valid email format but non-existent
            st.just(""),  # Empty string
            st.just("   "),  # Whitespace only
            st.just("not-an-email"),  # Malformed email
            st.just("@example.com"),  # Missing local part
            st.just("user@"),  # Missing domain
        ),
        password=st.one_of(
            st.text(min_size=0, max_size=100),  # Random text
            st.just(""),  # Empty password
            st.just("   "),  # Whitespace only
        )
    )
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=500  # Increase deadline due to bcrypt hashing
    )
    def test_property_invalid_credentials_rejection(self, db_session, email, password):
        """
        **Validates: Requirements 1.5**
        
        Feature: core-inventory, Property 3: Invalid Credentials Rejection
        
        For any invalid credentials (wrong password, non-existent email, or malformed input),
        authentication attempts should fail with a descriptive error message.
        """
        auth = Authenticator(db_session)
        
        # Create a known valid user for testing wrong password scenarios
        valid_email = "validuser@example.com"
        valid_password = "validpassword123"
        try:
            auth.signup(valid_email, valid_password, "Valid User")
        except AuthenticationError:
            # User might already exist from previous test iteration
            pass
        
        # Test login with invalid credentials
        # Case 1: Non-existent email (any email that's not the valid one)
        # Case 2: Wrong password (valid email but wrong password)
        # Case 3: Malformed input (empty, whitespace, invalid format)
        
        should_fail = False
        
        # Determine if this should fail
        if email != valid_email:
            # Non-existent email or malformed email
            should_fail = True
        elif email == valid_email and password != valid_password:
            # Valid email but wrong password
            should_fail = True
        
        if should_fail:
            # This should raise an AuthenticationError
            with pytest.raises(AuthenticationError) as exc_info:
                auth.login(email, password)
            
            # Verify error has descriptive message
            error = exc_info.value
            assert error.message is not None
            assert len(error.message) > 0
            assert error.code is not None
            assert error.code in [
                "INVALID_CREDENTIALS",
                "INVALID_EMAIL",
                "USER_NOT_FOUND"
            ]
        else:
            # This is the valid case - should succeed
            session = auth.login(email, password)
            assert session.id is not None
    
    @given(
        wrong_password=st.text(min_size=1, max_size=100).filter(lambda x: x != "correctpassword123")
    )
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=500  # Increase deadline due to bcrypt hashing
    )
    def test_property_wrong_password_always_fails(self, db_session, wrong_password):
        """
        **Validates: Requirements 1.5**
        
        Feature: core-inventory, Property 3: Invalid Credentials Rejection
        
        For any user with a known password, attempting to login with any other password
        should fail with a descriptive error message.
        """
        auth = Authenticator(db_session)
        
        # Create user with known password
        correct_email = "testuser@example.com"
        correct_password = "correctpassword123"
        
        try:
            auth.signup(correct_email, correct_password, "Test User")
        except AuthenticationError:
            # User might already exist
            pass
        
        # Try to login with wrong password
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login(correct_email, wrong_password)
        
        # Verify descriptive error
        error = exc_info.value
        assert error.message is not None
        assert len(error.message) > 0
        assert error.code == "INVALID_CREDENTIALS"
        assert "invalid" in error.message.lower() or "password" in error.message.lower()
    
    @given(
        nonexistent_email=st.emails()
    )
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=500  # Increase deadline due to bcrypt hashing
    )
    def test_property_nonexistent_email_always_fails(self, db_session, nonexistent_email):
        """
        **Validates: Requirements 1.5**
        
        Feature: core-inventory, Property 3: Invalid Credentials Rejection
        
        For any email that doesn't exist in the system, login attempts should fail
        with a descriptive error message.
        """
        auth = Authenticator(db_session)
        
        # Ensure this email doesn't exist by checking if it's not in our test set
        # We'll use a random password since the email doesn't exist anyway
        random_password = "somepassword123"
        
        # Try to login with non-existent email
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login(nonexistent_email, random_password)
        
        # Verify descriptive error
        error = exc_info.value
        assert error.message is not None
        assert len(error.message) > 0
        assert error.code == "INVALID_CREDENTIALS"
        assert "invalid" in error.message.lower()
    
    @given(
        malformed_input=st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t\n"),
            st.text(max_size=5).filter(lambda x: "@" not in x and "." not in x),
        )
    )
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=500  # Increase deadline due to bcrypt hashing
    )
    def test_property_malformed_input_always_fails(self, db_session, malformed_input):
        """
        **Validates: Requirements 1.5**
        
        Feature: core-inventory, Property 3: Invalid Credentials Rejection
        
        For any malformed input (empty strings, whitespace, invalid formats),
        authentication attempts should fail with a descriptive error message.
        """
        auth = Authenticator(db_session)
        
        # Try various malformed input scenarios
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login(malformed_input, "somepassword123")
        
        # Verify descriptive error
        error = exc_info.value
        assert error.message is not None
        assert len(error.message) > 0
        assert error.code in ["INVALID_CREDENTIALS", "INVALID_EMAIL"]
        assert "invalid" in error.message.lower() or "required" in error.message.lower()
    @given(
        malformed_input=st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t\n"),
            st.text(max_size=5).filter(lambda x: "@" not in x and "." not in x),
        )
    )
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=500  # Increase deadline due to bcrypt hashing
    )
    def test_property_malformed_input_always_fails(self, db_session, malformed_input):
        """
        **Validates: Requirements 1.5**
        
        Feature: core-inventory, Property 3: Invalid Credentials Rejection
        
        For any malformed input (empty strings, whitespace, invalid formats),
        authentication attempts should fail with a descriptive error message.
        """
        auth = Authenticator(db_session)
        
        # Try various malformed input scenarios
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login(malformed_input, "somepassword123")
        
        # Verify descriptive error
        error = exc_info.value
        assert error.message is not None
        assert len(error.message) > 0
        assert error.code in ["INVALID_CREDENTIALS", "INVALID_EMAIL"]
        assert "invalid" in error.message.lower() or "required" in error.message.lower()
    
    @given(
        email=st.emails(),
        password=st.text(min_size=8, max_size=100),
        name=st.text(min_size=1, max_size=100),
        num_validations=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=100, 
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000  # Increase deadline due to bcrypt hashing and multiple validations
    )
    def test_property_session_persistence(self, db_session, email, password, name, num_validations):
        """
        **Validates: Requirements 1.6, 14.4**
        
        Feature: core-inventory, Property 4: Session Persistence
        
        For any authenticated user session, subsequent requests using that session should
        remain valid until explicit logout.
        """
        auth = Authenticator(db_session)
        
        # Signup user
        try:
            user = auth.signup(email, password, name)
        except AuthenticationError:
            # User might already exist from previous test iteration, try to login instead
            try:
                session = auth.login(email, password)
                user = auth.validate_session(str(session.id))
            except AuthenticationError:
                # If login fails, the user exists but with different password
                # Skip this test case as it's not relevant to session persistence
                return
        else:
            # Login to create session
            session = auth.login(email, password)
        
        session_id = str(session.id)
        
        # Validate session multiple times - it should remain valid
        for i in range(num_validations):
            validated_user = auth.validate_session(session_id)
            
            # Verify the session returns the correct user
            assert validated_user.id == user.id
            assert validated_user.email == user.email
            assert validated_user.name == user.name
        
        # After multiple validations, session should still be valid
        final_validated_user = auth.validate_session(session_id)
        assert final_validated_user.id == user.id
        
        # Now logout
        auth.logout(session_id)
        
        # After logout, session should be invalid
        with pytest.raises(AuthenticationError) as exc_info:
            auth.validate_session(session_id)
        
        assert exc_info.value.code == "SESSION_NOT_FOUND"


class TestProfileManagementFlow:
    """Integration tests for profile management workflows."""
    
    def test_complete_profile_update_flow(self, db_session):
        """Test complete flow: signup -> get profile -> update profile -> verify."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("test@example.com", "password123", "Original Name")
        user_id = str(user.id)
        
        # Get profile
        profile = auth.get_profile(user_id)
        assert profile["name"] == "Original Name"
        assert profile["email"] == "test@example.com"
        
        # Update name
        updated_user = auth.update_profile(user_id, name="Updated Name")
        assert updated_user.name == "Updated Name"
        
        # Verify profile reflects update
        profile = auth.get_profile(user_id)
        assert profile["name"] == "Updated Name"
        
        # Update email
        updated_user = auth.update_profile(user_id, email="newemail@example.com")
        assert updated_user.email == "newemail@example.com"
        
        # Verify can login with new email
        session = auth.login("newemail@example.com", "password123")
        assert session.id is not None
    
    def test_complete_password_change_flow(self, db_session):
        """Test complete flow: signup -> change password -> login with new password."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("test@example.com", "oldpassword123", "Test User")
        user_id = str(user.id)
        
        # Change password
        auth.change_password(user_id, "oldpassword123", "newpassword123")
        
        # Verify can login with new password
        session = auth.login("test@example.com", "newpassword123")
        assert session.id is not None
        
        # Verify cannot login with old password
        with pytest.raises(AuthenticationError):
            auth.login("test@example.com", "oldpassword123")
    
    def test_profile_update_and_password_change_together(self, db_session):
        """Test updating profile and changing password in sequence."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("old@example.com", "oldpassword123", "Old Name")
        user_id = str(user.id)
        
        # Update profile
        auth.update_profile(user_id, name="New Name", email="new@example.com")
        
        # Change password
        auth.change_password(user_id, "oldpassword123", "newpassword123")
        
        # Verify can login with new email and new password
        session = auth.login("new@example.com", "newpassword123")
        assert session.id is not None
        
        # Verify profile has updated information
        validated_user = auth.validate_session(str(session.id))
        assert validated_user.name == "New Name"
        assert validated_user.email == "new@example.com"
    
    def test_multiple_profile_updates(self, db_session):
        """Test multiple sequential profile updates."""
        auth = Authenticator(db_session)
        
        # Signup
        user = auth.signup("test@example.com", "password123", "Name 1")
        user_id = str(user.id)
        
        # Update name multiple times
        auth.update_profile(user_id, name="Name 2")
        auth.update_profile(user_id, name="Name 3")
        auth.update_profile(user_id, name="Final Name")
        
        # Verify final state
        profile = auth.get_profile(user_id)
        assert profile["name"] == "Final Name"
    
    def test_profile_operations_with_active_session(self, db_session):
        """Test that profile operations work while user has active session."""
        auth = Authenticator(db_session)
        
        # Signup and login
        user = auth.signup("test@example.com", "password123", "Test User")
        session = auth.login("test@example.com", "password123")
        user_id = str(user.id)
        session_id = str(session.id)
        
        # Verify session is valid
        validated_user = auth.validate_session(session_id)
        assert validated_user.id == user.id
        
        # Update profile while session is active
        auth.update_profile(user_id, name="Updated Name")
        
        # Session should still be valid
        validated_user = auth.validate_session(session_id)
        assert validated_user.name == "Updated Name"
        
        # Change password while session is active
        auth.change_password(user_id, "password123", "newpassword123")
        
        # Existing session should still be valid (password change doesn't invalidate sessions)
        validated_user = auth.validate_session(session_id)
        assert validated_user.id == user.id
        
        # But new login requires new password
        new_session = auth.login("test@example.com", "newpassword123")
        assert new_session.id is not None
