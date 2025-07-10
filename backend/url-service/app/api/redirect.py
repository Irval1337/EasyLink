from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse
from datetime import datetime

from app.database import SessionDep
from app.crud.url import get_url_by_short_code, increment_click_count
from app.config import MAX_CUSTOM_URL_LENGTH

router = APIRouter()

@router.get("/{short_code}")
async def redirect_url(
    request: Request,
    session: SessionDep,
    short_code: str = Path(..., pattern=f"^[a-zA-Z0-9_-]{{4,{MAX_CUSTOM_URL_LENGTH}}}$"),
    password: str = Query(None, description="Password for protected URLs")
):
    url = get_url_by_short_code(session, short_code)
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if not url.is_active:
        raise HTTPException(status_code=410, detail="URL is no longer active")
    
    if url.expires_at and datetime.utcnow() > url.expires_at:
        url.is_active = False
        session.add(url)
        session.commit()
        raise HTTPException(status_code=410, detail="URL has expired")
    
    if url.password is not None:
        if password is None:
            raise HTTPException(
                status_code=401, 
                detail="Password required. Add password param"
            )
        if password != url.password:
            raise HTTPException(status_code=401, detail="Invalid password")
    
    increment_click_count(session, url)
    
    return RedirectResponse(url=url.original_url, status_code=301)
