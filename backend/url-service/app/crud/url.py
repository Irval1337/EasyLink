from sqlmodel import Session, select
from app.models.url import Url
from app.schemas.url import UrlCreate
from app.core.utils import generate_unique_short_code, validate_url, validate_custom_code
from datetime import datetime
from typing import Optional
from app.config import MAX_CUSTOM_URL_LENGTH

def create_url(session: Session, url_data: UrlCreate, user_id: int) -> Url:
    if not validate_url(str(url_data.original_url)):
        raise ValueError("Invalid URL format or URL too long")
    
    if url_data.custom_code:
        if not validate_custom_code(url_data.custom_code):
            raise ValueError(f"Invalid custom code: must be 4-{MAX_CUSTOM_URL_LENGTH} characters, alphanumeric with '_', '-' only, and not reserved")
        
        existing = session.exec(select(Url).where(Url.short_code == url_data.custom_code)).first()
        if existing:
            raise ValueError("Custom code already exists")
        short_code = url_data.custom_code
    else:
        short_code = generate_unique_short_code(session, str(url_data.original_url))
    
    url = Url(
        original_url=str(url_data.original_url),
        short_code=short_code,
        user_id=user_id,
        expires_at=url_data.expires_at
    )
    
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def get_url_by_short_code(session: Session, short_code: str) -> Optional[Url]:
    return session.exec(select(Url).where(Url.short_code == short_code)).first()

def increment_click_count(session: Session, url: Url) -> Url:
    url.click_count += 1
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def get_user_urls(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Url]:
    return session.exec(
        select(Url)
        .where(Url.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Url.created_at.desc())
    ).all()

def get_url_by_id(session: Session, url_id: int, user_id: Optional[int] = None) -> Optional[Url]:
    query = select(Url).where(Url.id == url_id)
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
    return session.exec(query).first()
