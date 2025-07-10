from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from datetime import timedelta
from pydantic import ValidationError

from app.database import SessionDep
from app.schemas.users import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.crud.users import (
    create_user, authenticate_user, update_user, logout_user,
    UserAlreadyExistsError, InvalidCredentialsError, InvalidCurrentPasswordError
)
from app.core.users import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, session: SessionDep):
    try:
        return create_user(session=session, user=user)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{e.field.capitalize()} '{e.value}' already registered"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, session: SessionDep):
    try:
        user = authenticate_user(session, user_credentials.identifier, user_credentials.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "version": user.token_version},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/me/update", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    try:
        return update_user(session=session, current_user=current_user, user_update=user_update)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{e.field.capitalize()} '{e.value}' already taken"
        )
    except InvalidCurrentPasswordError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/logout")
def logout(
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    logout_user(session=session, user=current_user)
    return {"message": "Successfully logged out"}

@router.post("/verify-token")
def verify_user_token(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.id, "valid": True}
