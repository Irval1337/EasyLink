from fastapi import APIRouter, HTTPException, Depends, status, Request, Path, Query
from fastapi.responses import RedirectResponse
from sqlmodel import select
from typing import Optional
from datetime import datetime

from app.database import SessionDep
from app.schemas.url import UrlCreate, UrlUpdate, UrlResponse, UrlListResponse
from app.crud.url import (
    create_url, get_url_by_short_code,
    get_user_urls, get_url_by_id, update_url, deactivate_url,
    get_url_with_qr_code, count_user_urls
)
from app.api.dependencies import get_current_user, get_current_user_optional

router = APIRouter()

def format_url_response(url, request: Request) -> UrlResponse:
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return UrlResponse(
        id=url.id,
        original_url=url.original_url,
        short_code=url.short_code,
        short_url=f"{base_url}/{url.short_code}",
        user_id=getattr(url, 'user_id', None),
        is_active=url.is_active,
        has_password=url.password is not None,
        created_at=url.created_at,
        expires_at=url.expires_at,
        remaining_clicks=url.remaining_clicks
    )

@router.post("/shorten", response_model=UrlResponse)
async def shorten_url(
    url_data: UrlCreate,
    request: Request,
    session: SessionDep,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    try:
        user_id = current_user["id"] if current_user else -1
        url = create_url(session, url_data, user_id)
        return format_url_response(url, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put("/{url_id}", response_model=UrlResponse)
async def update_url_endpoint(
    url_id: int,
    url_data: UrlUpdate,
    request: Request,
    session: SessionDep,
    current_user: dict = Depends(get_current_user)
):
    try:
        url = update_url(session, url_id, url_data, current_user["id"])
        if not url:
            raise HTTPException(status_code=404, detail="URL not found or access denied")
        return format_url_response(url, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{url_id}/deactivate", response_model=UrlResponse)
async def deactivate_url_endpoint(
    url_id: int,
    request: Request,
    session: SessionDep,
    current_user: dict = Depends(get_current_user)
):
    url = deactivate_url(session, url_id, current_user["id"])
    if not url:
        raise HTTPException(status_code=404, detail="URL not found or access denied")
    return format_url_response(url, request)

@router.get("/my", response_model=UrlListResponse)
async def get_my_urls(
    request: Request,
    session: SessionDep,
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    created_from: Optional[str] = Query(None),
    created_to: Optional[str] = Query(None),
    min_clicks: Optional[int] = Query(None, ge=0),
    max_clicks: Optional[int] = Query(None, ge=0),
    domain: Optional[str] = Query(None)
):
    created_from_dt = None
    created_to_dt = None
    
    if created_from:
        try:
            created_from_dt = datetime.fromisoformat(created_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_from date format. Use ISO format.")
    
    if created_to:
        try:
            created_to_dt = datetime.fromisoformat(created_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_to date format. Use ISO format.")
    
    urls = get_user_urls(
        session, 
        current_user["id"], 
        skip, 
        limit,
        is_active=is_active,
        created_from=created_from_dt,
        created_to=created_to_dt,
        domain=domain
    )
    
    if min_clicks is not None or max_clicks is not None:
        from app.crud.url import get_clicks_count_for_user_url
        token = None
        if hasattr(request, 'headers') and 'authorization' in request.headers:
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if token:
            filtered_urls = []
            for url in urls:
                clicks_count = await get_clicks_count_for_user_url(url.id, current_user["id"], token)
                if min_clicks is not None and clicks_count < min_clicks:
                    continue
                if max_clicks is not None and clicks_count > max_clicks:
                    continue
                filtered_urls.append(url)
            urls = filtered_urls
    
    total = count_user_urls(
        session,
        current_user["id"],
        is_active=is_active,
        created_from=created_from_dt,
        created_to=created_to_dt,
        domain=domain
    )
    formatted_urls = [format_url_response(url, request) for url in urls]
    
    return UrlListResponse(
        urls=formatted_urls, 
        total=total,
        skip=skip,
        limit=limit,
        filters={
            "is_active": is_active,
            "created_from": created_from,
            "created_to": created_to,
            "min_clicks": min_clicks,
            "max_clicks": max_clicks,
            "domain": domain
        }
    )

@router.get("/{url_id}/qr", response_model=dict)
async def get_url_qr_code(
    url_id: int,
    request: Request,
    session: SessionDep,
    current_user: dict = Depends(get_current_user)
):
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    result = get_url_with_qr_code(session, url_id, current_user["id"], base_url)
    if not result:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return {
        "url_id": result["url"].id,
        "short_code": result["url"].short_code,
        "short_url": result["short_url"],
        "qr_code": result["qr_code"]
    }
