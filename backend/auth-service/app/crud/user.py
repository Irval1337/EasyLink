from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.auth import get_password_hash, verify_password
import re

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
        hashed_password=hashed_password
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

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
    
    return user

def get_user_by_email_optional(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

def get_user_by_username_optional(session: Session, username: str) -> User | None:
    return session.exec(select(User).where(User.username == username)).first()

def get_user_by_id_optional(session: Session, user_id: int) -> User | None:
    return session.exec(select(User).where(User.id == user_id)).first()
