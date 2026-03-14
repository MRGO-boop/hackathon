"""Property-based tests for Authenticator profile management."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from core_inventory.components.authenticator import Authenticator, AuthenticationError
import uuid


# Custom strategies for generating test data
@st.composite
def valid_email(draw):
    """Generate valid email addresses with UUID to ensure uniqueness."""
    local = draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for uniqueness
    domain = draw(st.sampled_from(["example.com", "test.org", "demo.net", "mail.com"]))
    return f"{local}{unique_id}@{domain}"


@st.composite
def valid_password(draw):
    """Generate valid passwords (at least 8 characters)."""
    return draw(st.text(min_size=8, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%'))


@st.composite
def valid_name(draw):
    """Generate valid user names."""
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    first = draw(st.sampled_from(first_names))
    last = draw(st.sampled_from(last_names))
    return f"{first} {last}"


@st.composite
def profile_update_data(draw):
    """Generate profile update data (name and/or email)."""
    update_name = draw(st.booleans())
    update_email = draw(st.booleans())
    
    # Ensure at least one field is being updated
    if not update_name and not update_email:
        update_name = True
    
    data = {}
    if update_name:
        data["name"] = draw(valid_name())
    if update_email:
        data["email"] = draw(valid_email())
    
    return data


class TestPropertyProfileUpdatePersistence:
    """Property-based tests for profile update persistence."""
    
    @given(
        initial_email=valid_email(),
        initial_password=valid_password(),
        initial_name=valid_name(),
        updated_name=valid_name(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_33_profile_name_update_persistence(
        self, db_session, initial_email, initial_password, initial_name, updated_name
    ):
        """
        **Validates: Requirements 14.1, 14.2**
        
        Feature: core-inventory, Property 33: Profile Update Persistence
        
        For any user and updated profile data (name), updating the profile should
        persist the changes and make them retrievable in subsequent queries.
        """
        auth = Authenticator(db_session)
        
        # Create user
        try:
            user = auth.signup(initial_email, initial_password, initial_name)
        except AuthenticationError:
            # User might already exist from previous test iteration
            assume(False)
        
        user_id = str(user.id)
        
        # Verify initial profile
        profile = auth.get_profile(user_id)
        assert profile["name"] == initial_name
        assert profile["email"] == initial_email
        
        # Update name
        updated_user = auth.update_profile(user_id, name=updated_name)
        
        # Verify update was applied
        assert updated_user.name == updated_name
        assert updated_user.email == initial_email  # Email should remain unchanged
        
        # Verify persistence: retrieve profile again
        profile_after_update = auth.get_profile(user_id)
        assert profile_after_update["name"] == updated_name, \
            f"Name update did not persist: expected '{updated_name}', got '{profile_after_update['name']}'"
        assert profile_after_update["email"] == initial_email
        
        # Verify persistence: login and validate session
        session = auth.login(initial_email, initial_password)
        validated_user = auth.validate_session(str(session.id))
        assert validated_user.name == updated_name, \
            f"Name update not reflected in session validation: expected '{updated_name}', got '{validated_user.name}'"
    
    @given(
        initial_email=valid_email(),
        initial_password=valid_password(),
        initial_name=valid_name(),
        updated_email=valid_email(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_33_profile_email_update_persistence(
        self, db_session, initial_email, initial_password, initial_name, updated_email
    ):
        """
        **Validates: Requirements 14.1, 14.2**
        
        Feature: core-inventory, Property 33: Profile Update Persistence
        
        For any user and updated profile data (email), updating the profile should
        persist the changes and make them retrievable in subsequent queries.
        """
        auth = Authenticator(db_session)
        
        # Ensure emails are different
        assume(initial_email != updated_email)
        
        # Create user
        try:
            user = auth.signup(initial_email, initial_password, initial_name)
        except AuthenticationError:
            # User might already exist from previous test iteration
            assume(False)
        
        user_id = str(user.id)
        
        # Verify initial profile
        profile = auth.get_profile(user_id)
        assert profile["name"] == initial_name
        assert profile["email"] == initial_email
        
        # Update email
        try:
            updated_user = auth.update_profile(user_id, email=updated_email)
        except AuthenticationError as e:
            # Email might already be taken by another user
            if e.code == "EMAIL_EXISTS":
                assume(False)
            raise
        
        # Verify update was applied
        assert updated_user.name == initial_name  # Name should remain unchanged
        assert updated_user.email == updated_email
        
        # Verify persistence: retrieve profile again
        profile_after_update = auth.get_profile(user_id)
        assert profile_after_update["name"] == initial_name
        assert profile_after_update["email"] == updated_email, \
            f"Email update did not persist: expected '{updated_email}', got '{profile_after_update['email']}'"
        
        # Verify persistence: login with new email
        session = auth.login(updated_email, initial_password)
        validated_user = auth.validate_session(str(session.id))
        assert validated_user.email == updated_email, \
            f"Email update not reflected in login: expected '{updated_email}', got '{validated_user.email}'"
        
        # Verify old email no longer works
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login(initial_email, initial_password)
        assert exc_info.value.code == "INVALID_CREDENTIALS"
    
    @given(
        initial_email=valid_email(),
        initial_password=valid_password(),
        initial_name=valid_name(),
        updated_name=valid_name(),
        updated_email=valid_email(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1000
    )
    def test_property_33_profile_both_updates_persistence(
        self, db_session, initial_email, initial_password, initial_name, 
        updated_name, updated_email
    ):
        """
        **Validates: Requirements 14.1, 14.2**
        
        Feature: core-inventory, Property 33: Profile Update Persistence
        
        For any user and updated profile data (name and email), updating the profile
        should persist the changes and make them retrievable in subsequent queries.
        """
        auth = Authenticator(db_session)
        
        # Ensure emails are different
        assume(initial_email != updated_email)
        
        # Create user
        try:
            user = auth.signup(initial_email, initial_password, initial_name)
        except AuthenticationError:
            # User might already exist from previous test iteration
            assume(False)
        
        user_id = str(user.id)
        
        # Verify initial profile
        profile = auth.get_profile(user_id)
        assert profile["name"] == initial_name
        assert profile["email"] == initial_email
        
        # Update both name and email
        try:
            updated_user = auth.update_profile(user_id, name=updated_name, email=updated_email)
        except AuthenticationError as e:
            # Email might already be taken by another user
            if e.code == "EMAIL_EXISTS":
                assume(False)
            raise
        
        # Verify updates were applied
        assert updated_user.name == updated_name
        assert updated_user.email == updated_email
        
        # Verify persistence: retrieve profile again
        profile_after_update = auth.get_profile(user_id)
        assert profile_after_update["name"] == updated_name, \
            f"Name update did not persist: expected '{updated_name}', got '{profile_after_update['name']}'"
        assert profile_after_update["email"] == updated_email, \
            f"Email update did not persist: expected '{updated_email}', got '{profile_after_update['email']}'"
        
        # Verify persistence: login with new email
        session = auth.login(updated_email, initial_password)
        validated_user = auth.validate_session(str(session.id))
        assert validated_user.name == updated_name
        assert validated_user.email == updated_email
    
    @given(
        initial_email=valid_email(),
        initial_password=valid_password(),
        initial_name=valid_name(),
        new_password=valid_password(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000  # Increased deadline due to bcrypt hashing
    )
    def test_property_33_password_change_persistence(
        self, db_session, initial_email, initial_password, initial_name, new_password
    ):
        """
        **Validates: Requirements 14.3**
        
        Feature: core-inventory, Property 33: Profile Update Persistence
        
        For any user and updated password, changing the password should persist
        the changes and work for subsequent authentication attempts.
        """
        auth = Authenticator(db_session)
        
        # Ensure passwords are different
        assume(initial_password != new_password)
        
        # Create user
        try:
            user = auth.signup(initial_email, initial_password, initial_name)
        except AuthenticationError:
            # User might already exist from previous test iteration
            assume(False)
        
        user_id = str(user.id)
        
        # Verify can login with initial password
        session_before = auth.login(initial_email, initial_password)
        assert session_before.id is not None
        
        # Change password
        auth.change_password(user_id, initial_password, new_password)
        
        # Verify persistence: can login with new password
        session_after = auth.login(initial_email, new_password)
        assert session_after.id is not None
        
        validated_user = auth.validate_session(str(session_after.id))
        assert validated_user.id == user.id
        assert validated_user.email == initial_email
        
        # Verify old password no longer works
        with pytest.raises(AuthenticationError) as exc_info:
            auth.login(initial_email, initial_password)
        assert exc_info.value.code == "INVALID_CREDENTIALS"
    
    @given(
        initial_email=valid_email(),
        initial_password=valid_password(),
        initial_name=valid_name(),
        updated_name=valid_name(),
        updated_email=valid_email(),
        new_password=valid_password(),
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=1500
    )
    def test_property_33_complete_profile_update_persistence(
        self, db_session, initial_email, initial_password, initial_name,
        updated_name, updated_email, new_password
    ):
        """
        **Validates: Requirements 14.1, 14.2, 14.3**
        
        Feature: core-inventory, Property 33: Profile Update Persistence
        
        For any user and updated profile data (name, email, password), updating
        the profile should persist all changes and make them retrievable in
        subsequent queries or authentication attempts.
        """
        auth = Authenticator(db_session)
        
        # Ensure emails and passwords are different
        assume(initial_email != updated_email)
        assume(initial_password != new_password)
        
        # Create user
        try:
            user = auth.signup(initial_email, initial_password, initial_name)
        except AuthenticationError:
            # User might already exist from previous test iteration
            assume(False)
        
        user_id = str(user.id)
        
        # Verify initial state
        profile = auth.get_profile(user_id)
        assert profile["name"] == initial_name
        assert profile["email"] == initial_email
        
        session_initial = auth.login(initial_email, initial_password)
        assert session_initial.id is not None
        
        # Update name
        auth.update_profile(user_id, name=updated_name)
        
        # Update email
        try:
            auth.update_profile(user_id, email=updated_email)
        except AuthenticationError as e:
            # Email might already be taken by another user
            if e.code == "EMAIL_EXISTS":
                assume(False)
            raise
        
        # Change password
        auth.change_password(user_id, initial_password, new_password)
        
        # Verify all changes persisted: retrieve profile
        final_profile = auth.get_profile(user_id)
        assert final_profile["name"] == updated_name, \
            f"Name update did not persist: expected '{updated_name}', got '{final_profile['name']}'"
        assert final_profile["email"] == updated_email, \
            f"Email update did not persist: expected '{updated_email}', got '{final_profile['email']}'"
        
        # Verify all changes persisted: login with new email and new password
        final_session = auth.login(updated_email, new_password)
        validated_user = auth.validate_session(str(final_session.id))
        
        assert validated_user.id == user.id
        assert validated_user.name == updated_name
        assert validated_user.email == updated_email
        
        # Verify old credentials no longer work
        with pytest.raises(AuthenticationError):
            auth.login(initial_email, initial_password)
        
        with pytest.raises(AuthenticationError):
            auth.login(updated_email, initial_password)
        
        with pytest.raises(AuthenticationError):
            auth.login(initial_email, new_password)
    
    @given(
        initial_email=valid_email(),
        initial_password=valid_password(),
        initial_name=valid_name(),
        updates=st.lists(
            profile_update_data(),
            min_size=1,
            max_size=5
        )
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=2000
    )
    def test_property_33_multiple_sequential_updates_persistence(
        self, db_session, initial_email, initial_password, initial_name, updates
    ):
        """
        **Validates: Requirements 14.1, 14.2**
        
        Feature: core-inventory, Property 33: Profile Update Persistence
        
        For any user and sequence of profile updates, each update should persist
        and the final state should reflect all changes.
        """
        auth = Authenticator(db_session)
        
        # Create user
        try:
            user = auth.signup(initial_email, initial_password, initial_name)
        except AuthenticationError:
            # User might already exist from previous test iteration
            assume(False)
        
        user_id = str(user.id)
        
        # Track expected final state
        expected_name = initial_name
        expected_email = initial_email
        
        # Apply all updates
        for update_data in updates:
            try:
                if "name" in update_data and "email" in update_data:
                    auth.update_profile(user_id, name=update_data["name"], email=update_data["email"])
                    expected_name = update_data["name"]
                    expected_email = update_data["email"]
                elif "name" in update_data:
                    auth.update_profile(user_id, name=update_data["name"])
                    expected_name = update_data["name"]
                elif "email" in update_data:
                    auth.update_profile(user_id, email=update_data["email"])
                    expected_email = update_data["email"]
            except AuthenticationError as e:
                # Email might already be taken
                if e.code == "EMAIL_EXISTS":
                    continue
                raise
        
        # Verify final state persisted
        final_profile = auth.get_profile(user_id)
        assert final_profile["name"] == expected_name, \
            f"Final name did not persist: expected '{expected_name}', got '{final_profile['name']}'"
        assert final_profile["email"] == expected_email, \
            f"Final email did not persist: expected '{expected_email}', got '{final_profile['email']}'"
        
        # Verify can login with final email
        session = auth.login(expected_email, initial_password)
        validated_user = auth.validate_session(str(session.id))
        assert validated_user.name == expected_name
        assert validated_user.email == expected_email
