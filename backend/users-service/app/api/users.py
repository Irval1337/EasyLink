from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from datetime import timedelta
from pydantic import ValidationError
import logging

from app.database import SessionDep
from app.schemas.users import (
    UserCreate, UserLogin, UserResponse, Token, UserUpdate,
    EmailActivationRequest, ResendActivationRequest, EmailActivationResponse
)
from app.crud.users import (
    create_user, authenticate_user, update_user, logout_user,
    UserAlreadyExistsError, InvalidCredentialsError, InvalidCurrentPasswordError,
    EmailNotVerifiedError, get_user_by_email, UserNotFoundError,
    activate_user_email, resend_activation_email, EmailActivationCooldownError
)
from app.core.users import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.email import email_service
from app.config import SECRET_KEY
from app.api.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
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
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "version": user.token_version},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
    return {"message": "Token is valid", "user_id": current_user.id}

@router.get("/activate-email", response_model=EmailActivationResponse)
def activate_email(token: str, session: SessionDep):
    email = email_service.verify_email_activation_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation token"
        )
    
    try:
        user = activate_user_email(session, email)
        return EmailActivationResponse(
            message="Email successfully activated",
            success=True
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

@router.post("/resend-activation", response_model=EmailActivationResponse)
def resend_activation_email_endpoint(request: ResendActivationRequest, session: SessionDep):
    try:
        user = get_user_by_email(session, request.email)
        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        if resend_activation_email(session, user):
            return EmailActivationResponse(
                message="Activation email sent successfully"
            )
        return EmailActivationResponse(
                message="An unexpected error occurred while sending the email. Try again later."
            )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except EmailActivationCooldownError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {e.remaining_minutes} minutes before requesting another activation email"
        )
