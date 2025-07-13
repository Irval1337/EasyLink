from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse
from datetime import datetime
import httpx

from app.database import SessionDep
from app.crud.url import get_url_by_short_code
from app.config import MAX_CUSTOM_URL_LENGTH, ANALYTICS_SERVICE_URL

router = APIRouter()

async def track_click_event(request: Request, url_id: int, short_code: str):
    try:
        headers = dict(request.headers)
        payload = {
            "url_id": url_id,
            "user_agent": headers.get("user-agent", ""),
            "referer": headers.get("referer", "")
        }
        
        request_headers = {
            "Content-Type": "application/json"
        }
        
        auth_header = headers.get("authorization")
        if auth_header:
            request_headers["Authorization"] = auth_header
        
        real_ip = headers.get("x-real-ip") or headers.get("x-forwarded-for") or request.client.host
        if real_ip:
            request_headers["X-Real-IP"] = real_ip
            request_headers["X-Forwarded-For"] = real_ip
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ANALYTICS_SERVICE_URL}/events",
                json=payload,
                headers=request_headers,
                timeout=5.0
            )
    except Exception:
        pass

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
    
    await track_click_event(request, url.id, short_code)
    
    return RedirectResponse(url=url.original_url, status_code=301)
