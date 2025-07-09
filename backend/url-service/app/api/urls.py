from fastapi import APIRouter, HTTPException, Depends, status, Request, Path
from fastapi.responses import RedirectResponse
from sqlmodel import select
from typing import Optional
from datetime import datetime

from app.database import SessionDep
from app.schemas.url import UrlCreate, UrlResponse, UrlListResponse, UrlStats
from app.crud.url import (
    create_url, get_url_by_short_code, increment_click_count,
    get_user_urls, get_url_by_id
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
        click_count=url.click_count,
        is_active=url.is_active,
        created_at=url.created_at,
        expires_at=url.expires_at
    )

@router.post("/shorten", response_model=UrlResponse)
async def shorten_url(
    url_data: UrlCreate,
    request: Request,
    session: SessionDep,
    current_user: dict = Depends(get_current_user)
):
    try:
        url = create_url(session, url_data, current_user["id"])
        return format_url_response(url, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/my", response_model=UrlListResponse)
async def get_my_urls(
    request: Request,
    session: SessionDep,
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    urls = get_user_urls(session, current_user["id"], skip, limit)
    formatted_urls = [format_url_response(url, request) for url in urls]
    total = len(urls)
    return UrlListResponse(urls=formatted_urls, total=total)

@router.get("/stats/{url_id}", response_model=UrlStats)
async def get_url_stats(
    url_id: int,
    session: SessionDep,
    current_user: dict = Depends(get_current_user)
):
    url = get_url_by_id(session, url_id, None)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if url.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied: You can only view statistics for your own URLs")
    
    return UrlStats(
        id=url.id,
        original_url=url.original_url,
        short_code=url.short_code,
        click_count=url.click_count,
        created_at=url.created_at,
        expires_at=url.expires_at
    )
