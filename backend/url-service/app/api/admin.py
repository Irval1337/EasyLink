from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from app.database import SessionDep
from app.crud.url import check_and_deactivate_expired_urls, get_url_by_id
from app.api.dependencies import verify_admin_token
from app.schemas.url import UrlResponse
from sqlmodel import select, func
from app.models.url import Url

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
    is_active: Optional[bool] = Query(None)
):
    query = select(Url)
    
    if user_id is not None:
        query = query.where(Url.user_id == user_id)
    if is_active is not None:
        query = query.where(Url.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).scalar()
    
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
            "is_active": is_active
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
    session: SessionDep
):
    url = get_url_by_id(session, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"user_id": url.user_id}
