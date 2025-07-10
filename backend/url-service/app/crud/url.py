from sqlmodel import Session, select
from app.models.url import Url
from app.schemas.url import UrlCreate, UrlUpdate
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
        expires_at=url_data.expires_at,
        password=url_data.password
    )
    
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def update_url(session: Session, url_id: int, url_data: UrlUpdate, user_id: int) -> Optional[Url]:
    url = session.exec(select(Url).where(Url.id == url_id, Url.user_id == user_id)).first()
    if not url:
        return None
    
    if url_data.original_url is not None:
        if not validate_url(str(url_data.original_url)):
            raise ValueError("Invalid URL format or URL too long")
        url.original_url = str(url_data.original_url)
    
    if url_data.password is not None:
        url.password = url_data.password
    
    if url_data.expires_at is not None:
        url.expires_at = url_data.expires_at
    
    if url_data.is_active is not None:
        url.is_active = url_data.is_active
    
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def deactivate_url(session: Session, url_id: int, user_id: int) -> Optional[Url]:
    url = session.exec(select(Url).where(Url.id == url_id, Url.user_id == user_id)).first()
    if not url:
        return None
    
    url.is_active = False
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def get_url_by_short_code(session: Session, short_code: str) -> Optional[Url]:
    return session.exec(select(Url).where(Url.short_code == short_code)).first()

def check_and_deactivate_expired_urls(session: Session, user_id: Optional[int] = None) -> int:
    query = select(Url).where(
        Url.expires_at <= datetime.utcnow(),
        Url.is_active == True
    )
    
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
    
    expired_urls = session.exec(query).all()
    
    count = 0
    for url in expired_urls:
        url.is_active = False
        session.add(url)
        count += 1
    
    if count > 0:
        session.commit()
    
    return count

def increment_click_count(session: Session, url: Url) -> Url:
    url.click_count += 1
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def get_user_urls(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Url]:
    check_and_deactivate_expired_urls(session, user_id)
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
