from sqlmodel import Session, select
from app.models.url import Url
from app.schemas.url import UrlCreate, UrlUpdate
from app.core.utils import generate_unique_short_code, validate_url, validate_custom_code
from datetime import datetime
from typing import Optional
from app.config import MAX_CUSTOM_URL_LENGTH
import qrcode
import io
import base64

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
        password=url_data.password,
        remaining_clicks=url_data.remaining_clicks,
        hide_thumbnail=url_data.hide_thumbnail
    )
    
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def update_url(session: Session, url_id: int, url_data: UrlUpdate, user_id: int) -> Optional[Url]:
    if user_id == -1:
        return None
        
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
    
    if url_data.remaining_clicks:
        url.remaining_clicks = url_data.remaining_clicks
    
    if url_data.hide_thumbnail is not None:
        url.hide_thumbnail = url_data.hide_thumbnail
    
    session.add(url)
    session.commit()
    session.refresh(url)
    return url

def deactivate_url(session: Session, url_id: int, user_id: int) -> Optional[Url]:
    if user_id == -1:
        return None
        
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

def decrement_clicks_count(session: Session, url: Url) -> None:
    if url.remaining_clicks is None:
        return
    
    url.remaining_clicks -= 1
    if url.remaining_clicks <= 0:
        url.is_active = False
    
    session.add(url)
    session.commit()

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

def get_user_urls(
    session: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    domain: Optional[str] = None
) -> list[Url]:
    check_and_deactivate_expired_urls(session, user_id)
    
    query = select(Url).where(Url.user_id == user_id)
    
    if is_active is not None:
        query = query.where(Url.is_active == is_active)
    if created_from:
        query = query.where(Url.created_at >= created_from)
    if created_to:
        query = query.where(Url.created_at <= created_to)
    if domain:
        query = query.where(Url.original_url.contains(f"://{domain}"))
    
    return session.exec(
        query.offset(skip).limit(limit).order_by(Url.created_at.desc())
    ).all()

def count_user_urls(
    session: Session, 
    user_id: int,
    is_active: Optional[bool] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    domain: Optional[str] = None
) -> int:
    from sqlmodel import func
    
    query = select(func.count(Url.id)).where(Url.user_id == user_id)
    if is_active is not None:
        query = query.where(Url.is_active == is_active)
    if created_from:
        query = query.where(Url.created_at >= created_from)
    if created_to:
        query = query.where(Url.created_at <= created_to)
    if domain:
        query = query.where(Url.original_url.contains(f"://{domain}"))
    
    return session.exec(query).first() or 0

def get_url_by_id(session: Session, url_id: int, user_id: Optional[int] = None) -> Optional[Url]:
    query = select(Url).where(Url.id == url_id)
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
    return session.exec(query).first()

def generate_qr_code(url: str, size: int = 10, border: int = 4) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def get_url_with_qr_code(session: Session, url_id: int, user_id: int, base_url: str = "http://localhost:8000") -> Optional[dict]:
    if user_id == -1:
        return None
        
    url = session.exec(select(Url).where(Url.id == url_id, Url.user_id == user_id)).first()
    if not url:
        return None
    
    short_url = f"{base_url}/{url.short_code}"
    qr_code = generate_qr_code(short_url)
    return {
        "url": url,
        "short_url": short_url,
        "qr_code": qr_code
    }

async def get_clicks_count_for_user_url(url_id: int, user_id: int, token: str) -> int:
    try:
        import httpx
        from app.config import ANALYTICS_SERVICE_URL
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{ANALYTICS_SERVICE_URL}/my/clicks/url/{url_id}", headers=headers, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("total_clicks", 0)
            else:
                return 0
    except Exception:
        return 0
