from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import datetime
import httpx
import logging

from app.database import SessionDep
from app.crud.url import get_url_by_short_code, decrement_clicks_count
from app.config import MAX_CUSTOM_URL_LENGTH, ANALYTICS_SERVICE_URL
from app.core.rate_limiting import limiter, RATE_LIMIT_GENERAL

logger = logging.getLogger(__name__)
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
    except Exception as e:
        logger.error(f"Error sending click event to Analytics Service for URL {short_code}: {e}")

def is_social_media_bot(user_agent: str) -> bool:
    social_bots = [
        'facebookexternalhit', 'twitterbot', 'telegrambot', 'whatsapp',
        'skypebot', 'discordbot', 'slackbot', 'linkedinbot', 'vkshare',
        'applebot', 'googlebot', 'bingbot', 'yandexbot', 'viberbot',
        'facebot', 'ia_archiver', 'developers.google.com/+/web/snippet'
    ]
    user_agent_lower = user_agent.lower()
    return any(bot in user_agent_lower for bot in social_bots)

@router.get("/{short_code}")
@limiter.limit(RATE_LIMIT_GENERAL)
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
    
    if url.remaining_clicks is not None and url.remaining_clicks <= 0:
        url.is_active = False
        session.add(url)
        session.commit()
        raise HTTPException(status_code=410, detail="URL has reached maximum clicks limit")
    
    if url.password is not None:
        if password is None:
            raise HTTPException(
                status_code=401, 
                detail="Password required. Add password param"
            )
        if password != url.password:
            raise HTTPException(status_code=401, detail="Invalid password")
    
    user_agent = request.headers.get("user-agent", "")
    if is_social_media_bot(user_agent):
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        short_url = f"{base_url}/{short_code}"
        
        if url.hide_thumbnail:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>EasyLink - Сервис сокращения ссылок</title>
                <meta property="og:title" content="EasyLink - Сервис сокращения ссылок">
                <meta property="og:description" content="Это сокращенный URL-адрес, созданный с помощью EasyLink. Нажмите, чтобы перейти по ссылке.">
                <meta property="og:image" content="{base_url}/static/easylink-preview.png">
                <meta property="og:url" content="{short_url}">
                <meta property="og:type" content="website">
                <meta property="og:site_name" content="EasyLink">
                <meta name="twitter:card" content="summary_large_image">
                <meta name="twitter:title" content="EasyLink - Сервис сокращения ссылок">
                <meta name="twitter:description" content="Это сокращенный URL-адрес, созданный с помощью EasyLink. Нажмите, чтобы перейти по ссылке.">
                <meta name="twitter:image" content="{base_url}/static/easylink-preview.png">
                <meta http-equiv="refresh" content="0; url={url.original_url}">
            </head>
            <body>
                <p>Redirecting to destination...</p>
                <p>Если вы не перенаправлены автоматически, <a href="{url.original_url}">нажмите здесь</a>.</p>
            </body>
            </html>
            """
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Переадресация...</title>
                <meta http-equiv="refresh" content="0; url={url.original_url}">
                <link rel="canonical" href="{url.original_url}">
            </head>
            <body>
                <p>Переадресация...</p>
                <p>Если вы не перенаправлены автоматически, <a href="{url.original_url}">нажмите здесь</a>.</p>
            </body>
            </html>
            """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    
    decrement_clicks_count(session, url)
    session.refresh(url)
    await track_click_event(request, url.id, short_code)
    
    return RedirectResponse(url=url.original_url, status_code=301)
