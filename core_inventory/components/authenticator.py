"""Authenticator component for user authentication and authorization."""
import bcrypt
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from core_inventory.models.user import User
from core_inventory.models.session import Session as UserSession
from core_inventory.models.password_reset import PasswordReset


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class Authenticator:
    """Handles user authentication, session management, and password reset."""
    
    def __init__(self, db: Session):
        """Initialize authenticator with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def signup(self, email: str, password: str, name: str) -> User:
        """Create a new user account with email and password.
        
        Args:
            email: User's email address (must be unique)
            password: User's password (will be hashed)
            name: User's full name
            
        Returns:
            User: The newly created user object
            
        Raises:
            AuthenticationError: If email already exists or validation fails
        """
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
        existing_user = self.db.query(User).filter(User.email == email.strip().lower()).first()
        if existing_user:
            raise AuthenticationError(
                f"Email {email} is already registered",
                "EMAIL_EXISTS",
                {"email": email}
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email=email.strip().lower(),
            password_hash=password_hash,
            name=name.strip()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def login(self, email: str, password: str) -> UserSession:
        """Authenticate user and create a session.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            UserSession: The newly created session object
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Validate input
        if not email or not email.strip():
            raise AuthenticationError(
                "Email is required",
                "INVALID_CREDENTIALS",
                {"field": "email"}
            )
        
        if not password:
            raise AuthenticationError(
                "Password is required",
                "INVALID_CREDENTIALS",
                {"field": "password"}
            )
        
        # Find user
        user = self.db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            raise AuthenticationError(
                "Invalid email or password",
                "INVALID_CREDENTIALS"
            )
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise AuthenticationError(
                "Invalid email or password",
                "INVALID_CREDENTIALS"
            )
        
        # Create session (expires in 24 hours)
        session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def validate_session(self, session_id: str) -> User:
        """Validate a session and return the associated user.
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            User: The user associated with the session
            
        Raises:
            AuthenticationError: If session is invalid or expired
        """
        if not session_id:
            raise AuthenticationError(
                "Session ID is required",
                "INVALID_SESSION"
            )
        
        # Parse session ID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise AuthenticationError(
                "Invalid session ID format",
                "INVALID_SESSION",
                {"session_id": session_id}
            )
        
        # Find session
        session = self.db.query(UserSession).filter(UserSession.id == session_uuid).first()
        if not session:
            raise AuthenticationError(
                "Session not found",
                "SESSION_NOT_FOUND",
                {"session_id": session_id}
            )
        
        # Check if session is expired
        if session.expires_at < datetime.utcnow():
            raise AuthenticationError(
                "Session has expired",
                "SESSION_EXPIRED",
                {"session_id": session_id, "expired_at": session.expires_at.isoformat()}
            )
        
        # Get user
        user = self.db.query(User).filter(User.id == session.user_id).first()
        if not user:
            raise AuthenticationError(
                "User not found for session",
                "USER_NOT_FOUND",
                {"session_id": session_id}
            )
        
        return user
    
    def request_password_reset(self, email: str) -> str:
        """Request a password reset by generating and storing an OTP.
        
        Args:
            email: User's email address
            
        Returns:
            str: The generated OTP (6-digit code)
            
        Raises:
            AuthenticationError: If email is not found
        """
        if not email or not email.strip():
            raise AuthenticationError(
                "Email is required",
                "INVALID_EMAIL",
                {"field": "email"}
            )
        
        # Find user
        user = self.db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            raise AuthenticationError(
                f"No account found with email {email}",
                "USER_NOT_FOUND",
                {"email": email}
            )
        
        # Generate 6-digit OTP
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Create password reset record (expires in 15 minutes)
        password_reset = PasswordReset(
            id=uuid.uuid4(),
            user_id=user.id,
            otp=otp,
            is_used=False,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        
        self.db.add(password_reset)
        self.db.commit()
        
        # In a real system, this would send an email
        # For now, we return the OTP for testing purposes
        return otp
    
    def reset_password(self, otp: str, new_password: str) -> None:
        """Reset password using a valid OTP.
        
        Args:
            otp: The one-time password received via email
            new_password: The new password to set
            
        Raises:
            AuthenticationError: If OTP is invalid, expired, or already used
        """
        if not otp or not otp.strip():
            raise AuthenticationError(
                "OTP is required",
                "INVALID_OTP",
                {"field": "otp"}
            )
        
        if not new_password or len(new_password) < 8:
            raise AuthenticationError(
                "Password must be at least 8 characters long",
                "INVALID_PASSWORD",
                {"field": "password", "min_length": 8}
            )
        
        # Find password reset record
        password_reset = self.db.query(PasswordReset).filter(
            PasswordReset.otp == otp.strip(),
            PasswordReset.is_used == False
        ).first()
        
        if not password_reset:
            raise AuthenticationError(
                "Invalid or already used OTP",
                "INVALID_OTP"
            )
        
        # Check if OTP is expired
        if password_reset.expires_at < datetime.utcnow():
            raise AuthenticationError(
                "OTP has expired",
                "OTP_EXPIRED",
                {"expired_at": password_reset.expires_at.isoformat()}
            )
        
        # Get user
        user = self.db.query(User).filter(User.id == password_reset.user_id).first()
        if not user:
            raise AuthenticationError(
                "User not found",
                "USER_NOT_FOUND"
            )
        
        # Hash new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user password
        user.password_hash = password_hash
        
        # Mark OTP as used
        password_reset.is_used = True
        
        self.db.commit()
    
    def logout(self, session_id: str) -> None:
        """Terminate a user session.
        
        Args:
            session_id: The session ID to terminate
            
        Raises:
            AuthenticationError: If session is not found
        """
        if not session_id:
            raise AuthenticationError(
                "Session ID is required",
                "INVALID_SESSION"
            )
        
        # Parse session ID
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise AuthenticationError(
                "Invalid session ID format",
                "INVALID_SESSION",
                {"session_id": session_id}
            )
        
        # Find and delete session
        session = self.db.query(UserSession).filter(UserSession.id == session_uuid).first()
        if not session:
            raise AuthenticationError(
                "Session not found",
                "SESSION_NOT_FOUND",
                {"session_id": session_id}
            )
        
        self.db.delete(session)
        self.db.commit()
    
    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict containing user profile information (name, email)
            
        Raises:
            AuthenticationError: If user is not found
        """
        if not user_id:
            raise AuthenticationError(
                "User ID is required",
                "INVALID_USER_ID",
                {"field": "user_id"}
            )
        
        # Parse user ID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise AuthenticationError(
                "Invalid user ID format",
                "INVALID_USER_ID",
                {"user_id": user_id}
            )
        
        # Find user
        user = self.db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise AuthenticationError(
                "User not found",
                "USER_NOT_FOUND",
                {"user_id": user_id}
            )
        
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        }
    
    def update_profile(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> User:
        """Update user profile information (name and/or email).
        
        Args:
            user_id: The user's ID
            name: New name (optional)
            email: New email (optional)
            
        Returns:
            User: The updated user object
            
        Raises:
            AuthenticationError: If user is not found or validation fails
        """
        if not user_id:
            raise AuthenticationError(
                "User ID is required",
                "INVALID_USER_ID",
                {"field": "user_id"}
            )
        
        # Parse user ID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise AuthenticationError(
                "Invalid user ID format",
                "INVALID_USER_ID",
                {"user_id": user_id}
            )
        
        # Find user
        user = self.db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise AuthenticationError(
                "User not found",
                "USER_NOT_FOUND",
                {"user_id": user_id}
            )
        
        # Update name if provided
        if name is not None:
            if not name.strip():
                raise AuthenticationError(
                    "Name cannot be empty",
                    "INVALID_NAME",
                    {"field": "name"}
                )
            user.name = name.strip()
        
        # Update email if provided
        if email is not None:
            if not email.strip():
                raise AuthenticationError(
                    "Email cannot be empty",
                    "INVALID_EMAIL",
                    {"field": "email"}
                )
            
            normalized_email = email.strip().lower()
            
            # Check if email is already taken by another user
            existing_user = self.db.query(User).filter(
                User.email == normalized_email,
                User.id != user_uuid
            ).first()
            
            if existing_user:
                raise AuthenticationError(
                    f"Email {email} is already taken",
                    "EMAIL_EXISTS",
                    {"email": email}
                )
            
            user.email = normalized_email
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """Change user password with validation of current password.
        
        Args:
            user_id: The user's ID
            current_password: The user's current password
            new_password: The new password to set
            
        Raises:
            AuthenticationError: If user is not found, current password is wrong, or validation fails
        """
        if not user_id:
            raise AuthenticationError(
                "User ID is required",
                "INVALID_USER_ID",
                {"field": "user_id"}
            )
        
        # Parse user ID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise AuthenticationError(
                "Invalid user ID format",
                "INVALID_USER_ID",
                {"user_id": user_id}
            )
        
        # Find user
        user = self.db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise AuthenticationError(
                "User not found",
                "USER_NOT_FOUND",
                {"user_id": user_id}
            )
        
        # Validate current password
        if not current_password:
            raise AuthenticationError(
                "Current password is required",
                "INVALID_PASSWORD",
                {"field": "current_password"}
            )
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise AuthenticationError(
                "Current password is incorrect",
                "INVALID_CREDENTIALS",
                {"field": "current_password"}
            )
        
        # Validate new password
        if not new_password or len(new_password) < 8:
            raise AuthenticationError(
                "New password must be at least 8 characters long",
                "INVALID_PASSWORD",
                {"field": "new_password", "min_length": 8}
            )
        
        # Hash and update password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.password_hash = password_hash
        
        self.db.commit()
