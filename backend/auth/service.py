"""Authentication service."""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from loguru import logger

from database.models import User
from core.security import SecurityService
from core.exceptions import AuthenticationError, ConflictError, NotFoundError
from .schemas import UserCreate, UserUpdate


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: Session):
        """Initialize auth service."""
        self.db = db
        self.security = SecurityService()
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
            
        Raises:
            ConflictError: If username already exists
        """
        # Check if user exists
        existing_user = self.db.query(User).filter(
            User.username == user_data.username
        ).first()
        
        if existing_user:
            raise ConflictError(f"Username '{user_data.username}' already exists")
        
        # Create new user
        password_hash = self.security.get_password_hash(user_data.password)
        
        new_user = User(
            username=user_data.username,
            password_hash=password_hash,
            full_name=user_data.full_name,
            department=user_data.department
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        logger.info(f"Created new user: {new_user.username}")
        return new_user
    
    def authenticate_user(self, username: str, password: str) -> User:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authenticated user
            
        Raises:
            AuthenticationError: If authentication fails
        """
        user = self.db.query(User).filter(
            User.username == username
        ).first()
        
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            raise AuthenticationError("Invalid username or password")
        
        if not self.security.verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for user: {username}")
            raise AuthenticationError("Invalid username or password")
        
        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {username}")
            raise AuthenticationError("User account is inactive")
        
        logger.info(f"User authenticated: {username}")
        return user
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            NotFoundError: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        return user
    
    def update_user(self, user_id: int, update_data: UserUpdate) -> User:
        """
        Update user information.
        
        Args:
            user_id: User ID
            update_data: Update data
            
        Returns:
            Updated user
            
        Raises:
            NotFoundError: If user not found
        """
        user = self.get_user_by_id(user_id)
        
        # Update fields if provided
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        
        if update_data.department is not None:
            user.department = update_data.department
        
        if update_data.password is not None:
            user.password_hash = self.security.get_password_hash(update_data.password)
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Updated user: {user.username}")
        return user