from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.users import UserCreate, UserUpdate
from app.core.users import get_password_hash, verify_password
from app.core.email import email_service
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)

class UserAlreadyExistsError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"{field.capitalize()} '{value}' already exists")

class UserNotFoundError(Exception):
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"User with {identifier} not found")

class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Invalid credentials")

class InvalidCurrentPasswordError(Exception):
    def __init__(self):
        super().__init__("Current password is incorrect")

class EmailNotVerifiedError(Exception):
    def __init__(self):
        super().__init__("Email is not verified")

class EmailActivationCooldownError(Exception):
    def __init__(self, remaining_minutes: int):
        self.remaining_minutes = remaining_minutes
        super().__init__(f"Please wait {remaining_minutes} minutes before requesting another activation email")

def is_email(identifier: str) -> bool:
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, identifier))

def create_user(session: Session, user: UserCreate) -> User:
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise UserAlreadyExistsError("email", user.email)
    
    existing_user = session.exec(select(User).where(User.username == user.username)).first()
    if existing_user:
        raise UserAlreadyExistsError("username", user.username)
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        email_verified=False,
        token_version=1
    )
    
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        success = email_service.send_activation_email(db_user.email, db_user.username)
        
        if success:
            db_user.last_activation_email_sent = datetime.utcnow()
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
        else:
            logger.error(f"Failed to send activation email to: {user.email}")
        
        return db_user
    except Exception as e:
        logger.error(f"Error creating user {user.email}: {e}")
        session.rollback()
        raise

def update_user(session: Session, current_user: User, user_update: UserUpdate) -> User:
    if not verify_password(user_update.current_password, current_user.hashed_password):
        raise InvalidCurrentPasswordError()
    
    invalidate_tokens = False
    send_activation_email = False
    
    if user_update.email is not None:
        existing_user = session.exec(select(User).where(User.email == user_update.email)).first()
        if existing_user and existing_user.id != current_user.id:
            raise UserAlreadyExistsError("email", user_update.email)
        current_user.email = user_update.email
        current_user.email_verified = False
        invalidate_tokens = True
        send_activation_email = True
    
    if user_update.username is not None:
        existing_user = session.exec(select(User).where(User.username == user_update.username)).first()
        if existing_user and existing_user.id != current_user.id:
            raise UserAlreadyExistsError("username", user_update.username)
        current_user.username = user_update.username
    
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
        invalidate_tokens = True
    
    if invalidate_tokens:
        current_user.token_version += 1
    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    if send_activation_email:
        email_service.send_activation_email(current_user.email, current_user.username)
    return current_user

def logout_user(session: Session, user: User) -> None:
    user.token_version += 1
    session.add(user)
    session.commit()

def get_user_by_email(session: Session, email: str) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise UserNotFoundError(f"email '{email}'")
    return user

def get_user_by_username(session: Session, username: str) -> User:
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise UserNotFoundError(f"username '{username}'")
    return user

def get_user_by_id(session: Session, user_id: int) -> User:
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise UserNotFoundError(f"id '{user_id}'")
    return user

def authenticate_user(session: Session, identifier: str, password: str) -> User:
    try:
        if is_email(identifier):
            user = get_user_by_email(session, identifier)
        else:
            user = get_user_by_username(session, identifier)
    except UserNotFoundError:
        raise InvalidCredentialsError()
    
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    if not user.email_verified:
        raise EmailNotVerifiedError()
    
    return user

def get_user_by_email_optional(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

def get_user_by_username_optional(session: Session, username: str) -> User | None:
    return session.exec(select(User).where(User.username == username)).first()

def get_user_by_id_optional(session: Session, user_id: int) -> User | None:
    return session.exec(select(User).where(User.id == user_id)).first()

def activate_user_email(session: Session, email: str) -> User:
    user = get_user_by_email(session, email)
    user.email_verified = True
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def can_resend_activation_email(session: Session, user: User) -> bool:
    from app.config import EMAIL_ACTIVATION_RESEND_COOLDOWN_MINUTES
    if user.last_activation_email_sent is None:
        return True
    
    cooldown_time = user.last_activation_email_sent + timedelta(minutes=EMAIL_ACTIVATION_RESEND_COOLDOWN_MINUTES)
    return datetime.utcnow() > cooldown_time

def get_activation_email_cooldown_remaining(session: Session, user: User) -> int:
    from app.config import EMAIL_ACTIVATION_RESEND_COOLDOWN_MINUTES
    if user.last_activation_email_sent is None:
        return 0
    
    cooldown_time = user.last_activation_email_sent + timedelta(minutes=EMAIL_ACTIVATION_RESEND_COOLDOWN_MINUTES)
    remaining = cooldown_time - datetime.utcnow()
    if remaining.total_seconds() <= 0:
        return 0
    
    return int(remaining.total_seconds() / 60) + 1

def resend_activation_email(session: Session, user: User) -> bool:
    if not can_resend_activation_email(session, user):
        remaining = get_activation_email_cooldown_remaining(session, user)
        raise EmailActivationCooldownError(remaining)
    
    success = email_service.send_activation_email(user.email, user.username)
    if not success:
        logger.error(f"Could not resend activation email to user: {user.email}")
        return False
    user.last_activation_email_sent = datetime.utcnow()
    session.add(user)
    session.commit()
    return True