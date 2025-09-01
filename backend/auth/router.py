"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from database.session import get_db
from database.models import User
from core.security import SecurityService
from core.middleware import APIResponse
from .schemas import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate
from .service import AuthService
from .dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        JWT token and user information
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.create_user(user_data)
        
        # Generate token
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = SecurityService.create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user.
    
    Args:
        login_data: Login credentials
        db: Database session
        
    Returns:
        JWT token and user information
    """
    try:
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(
            login_data.username,
            login_data.password
        )
        
        # Generate token
        token_data = {"sub": str(user.id), "username": user.username}
        access_token = SecurityService.create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile.
    
    Args:
        update_data: Profile update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    try:
        auth_service = AuthService(db)
        updated_user = auth_service.update_user(current_user.id, update_data)
        return UserResponse.from_orm(updated_user)
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (client-side token removal).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.username}")
    return APIResponse.success(message="Logged out successfully")