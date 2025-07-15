from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse
import httpx
import logging
from app.database import SessionDep
from app.crud.url import check_and_deactivate_expired_urls, get_url_by_id
from app.api.dependencies import verify_admin_token
from app.schemas.url import UrlResponse
from sqlmodel import select, func
from app.models.url import Url
from app.config import ADMIN_TOKEN, ANALYTICS_SERVICE_URL

logger = logging.getLogger(__name__)
router = APIRouter()

def format_url_response(url, request: Request) -> UrlResponse:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return UrlResponse(
        id=url.id,
        original_url=url.original_url,
        short_code=url.short_code,
        short_url=f"{base_url}/{url.short_code}",
        user_id=url.user_id,
        is_active=url.is_active,
        has_password=url.password is not None,
        created_at=url.created_at,
        expires_at=url.expires_at,
        remaining_clicks=url.remaining_clicks
    )

async def get_clicks_count_for_url(url_id: int) -> int:
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
            response = await client.get(f"{ANALYTICS_SERVICE_URL}/admin/clicks/url/{url_id}", headers=headers, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("total_clicks", 0)
            else:
                logger.warning(f"Failed to get clicks for URL {url_id}: {response.status_code}")
                return 0
    except Exception as e:
        logger.error(f"Error getting clicks for URL {url_id}: {str(e)}")
        return 0

@router.post("/cleanup-expired")
async def cleanup_expired_urls(
    session: SessionDep,
    admin_verified: bool = Depends(verify_admin_token)
):
    count = check_and_deactivate_expired_urls(session)
    return {"message": f"Deactivated {count} URLs"}

@router.get("/urls")
async def get_all_urls(
    request: Request,
    session: SessionDep,
    admin_verified: bool = Depends(verify_admin_token),
    user_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    created_from: Optional[str] = Query(None),
    created_to: Optional[str] = Query(None),
    min_clicks: Optional[int] = Query(None, ge=0),
    max_clicks: Optional[int] = Query(None, ge=0),
    domain: Optional[str] = Query(None)
):
    query = select(Url)
    
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
    if is_active is not None:
        query = query.where(Url.is_active == is_active)
    
    if created_from:
        try:
            created_from_dt = datetime.fromisoformat(created_from.replace('Z', '+00:00'))
            query = query.where(Url.created_at >= created_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_from date format. Use ISO format.")
    
    if created_to:
        try:
            created_to_dt = datetime.fromisoformat(created_to.replace('Z', '+00:00'))
            query = query.where(Url.created_at <= created_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_to date format. Use ISO format.")
    
    if domain:
        query = query.where(Url.original_url.contains(f"://{domain}"))
    
    count_query = select(func.count(Url.id))
    if user_id is not None:
        count_query = count_query.where(Url.user_id == user_id)
    if is_active is not None:
        count_query = count_query.where(Url.is_active == is_active)
    if created_from:
        try:
            created_from_dt = datetime.fromisoformat(created_from.replace('Z', '+00:00'))
            count_query = count_query.where(Url.created_at >= created_from_dt)
        except ValueError:
            pass
    if created_to:
        try:
            created_to_dt = datetime.fromisoformat(created_to.replace('Z', '+00:00'))
            count_query = count_query.where(Url.created_at <= created_to_dt)
        except ValueError:
            pass
    if domain:
        count_query = count_query.where(Url.original_url.contains(f"://{domain}"))
    
    total_count = session.exec(count_query).first()
    
    if min_clicks is not None or max_clicks is not None:
        all_urls = session.exec(query.order_by(Url.created_at.desc())).all()
        
        filtered_urls = []
        for url in all_urls:
            clicks_count = await get_clicks_count_for_url(url.id)
            if min_clicks is not None and clicks_count < min_clicks:
                continue
            if max_clicks is not None and clicks_count > max_clicks:
                continue
            filtered_urls.append(url)
        total_count = len(filtered_urls)
        urls = filtered_urls[skip:skip + limit]
    else:
        query = query.order_by(Url.created_at.desc()).offset(skip).limit(limit)
        urls = session.exec(query).all()
    
    formatted_urls = [format_url_response(url, request) for url in urls]
    return {
        "urls": formatted_urls,
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "filters": {
            "user_id": user_id,
            "is_active": is_active,
            "created_from": created_from,
            "created_to": created_to,
            "min_clicks": min_clicks,
            "max_clicks": max_clicks,
            "domain": domain
        }
    }

@router.get("/urls/{url_id}")
async def get_url_by_id_admin(
    url_id: int,
    request: Request,
    session: SessionDep,
    admin_verified: bool = Depends(verify_admin_token)
):
    url = get_url_by_id(session, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return format_url_response(url, request)

@router.get("/urls/{url_id}/user-id")
async def get_url_user_id(
    url_id: int,
    session: SessionDep,
    admin_verified: bool = Depends(verify_admin_token)
):
    url = get_url_by_id(session, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"user_id": url.user_id}
