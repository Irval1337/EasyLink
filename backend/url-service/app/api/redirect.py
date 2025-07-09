from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import RedirectResponse
from datetime import datetime
import re

from app.database import SessionDep
from app.crud.url import get_url_by_short_code, increment_click_count

from app.config import MAX_CUSTOM_URL_LENGTH

router = APIRouter()

@router.get("/{short_code}")
async def redirect_url(
    session: SessionDep,
    short_code: str = Path(..., pattern=f"^[a-zA-Z0-9_-]{4,MAX_CUSTOM_URL_LENGTH}$")
):
    url = get_url_by_short_code(session, short_code)
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if not url.is_active:
        raise HTTPException(status_code=410, detail="URL is no longer active")
    
    if url.expires_at and datetime.utcnow() > url.expires_at:
        raise HTTPException(status_code=410, detail="URL has expired")
    
    increment_click_count(session, url)
    
    return RedirectResponse(url=url.original_url, status_code=301)
