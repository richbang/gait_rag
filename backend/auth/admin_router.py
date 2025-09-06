"""Admin router for user management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.session import get_db
from database.models import User
from auth.dependencies import get_current_user
from auth.schemas import UserCreate, UserUpdate, UserResponse
from auth.service import AuthService
from loguru import logger

router = APIRouter()


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify that the current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    logger.info(f"Admin {admin.username} listed {len(users)} users")
    return users


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create a new user (admin only)."""
    auth_service = AuthService(db)
    
    # Check if username exists
    existing_user = db.query(User).filter_by(username=user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    new_user = auth_service.create_user(
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        department=user_data.department
    )
    
    if user_data.is_admin:
        new_user.is_admin = True
        db.commit()
    
    logger.info(f"Admin {admin.username} created user {new_user.username}")
    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update a user (admin only)."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.department is not None:
        user.department = user_data.department
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    # Update password if provided
    if user_data.password:
        auth_service = AuthService(db)
        user.password_hash = auth_service.hash_password(user_data.password)
    
    db.commit()
    logger.info(f"Admin {admin.username} updated user {user.username}")
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Delete a user (admin only)."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting the last admin
    if user.is_admin:
        admin_count = db.query(User).filter_by(is_admin=True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user"
            )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    logger.info(f"Admin {admin.username} deleted user {username}")
    return {"message": f"User {username} deleted successfully"}


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Toggle user active status (admin only)."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating self
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = not user.is_active
    db.commit()
    
    status_text = "activated" if user.is_active else "deactivated"
    logger.info(f"Admin {admin.username} {status_text} user {user.username}")
    return {"message": f"User {user.username} {status_text}", "is_active": user.is_active}