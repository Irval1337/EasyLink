from fastapi import APIRouter, HTTPException, Depends, Request, Response
from typing import Optional
from datetime import datetime
import httpx

from app.database import SessionDep
from app.schemas.analytics import ClickEventCreate, ClickEventResponse
from app.crud.analytics import create_click_event
from app.core.analytics import parse_user_agent, get_location_info, extract_real_ip
from app.core.stats import calculate_stats
from app.core.export import export_stats_to_json, export_stats_to_csv, export_clicks_to_json, export_clicks_to_csv
from app.api.dependencies import get_current_user, get_current_user_optional
from app.config import URL_SERVICE_URL, ADMIN_TOKEN

router = APIRouter()

@router.post("/events", response_model=ClickEventResponse)
async def track_click(
    request: Request,
    click_data: ClickEventCreate,
    session: SessionDep,
    user_data: Optional[dict] = Depends(get_current_user_optional)
):
    headers = dict(request.headers)
    real_ip = extract_real_ip(headers)
    
    user_agent_info = parse_user_agent(click_data.user_agent)
    location_info = await get_location_info(real_ip)
    
    user_id = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL_SERVICE_URL}/admin/urls/{click_data.url_id}/user-id",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
                timeout=5.0
            )
            if response.status_code == 200:
                url_data = response.json()
                user_id = url_data.get("user_id")
    except Exception:
        pass
    
    event_data = {
        "url_id": click_data.url_id,
        "user_id": user_id,
        "ip_address": real_ip,
        "user_agent": click_data.user_agent,
        "referer": click_data.referer,
        "country": location_info.get("country"),
        "city": location_info.get("city"),
        "device_type": user_agent_info.get("device_type"),
        "browser": user_agent_info.get("browser"),
        "os": user_agent_info.get("os")
    }
    
    event = create_click_event(session, event_data)
    
    return event

@router.get("/stats")
async def get_analytics(
    session: SessionDep,
    user_data: dict = Depends(get_current_user),
    url_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    selected_date: Optional[str] = None
):
    user_id = user_data.get("id")
    token = user_data.get("token")
    
    user_url_ids = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL_SERVICE_URL}/my?skip=0&limit=1000",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get user URLs")
            
            user_urls_response = response.json()
            user_urls = user_urls_response.get("urls", [])
            user_url_ids = [url["id"] for url in user_urls]
            
            if url_id and url_id not in user_url_ids:
                url_id = None
    except Exception:
        pass
    
    now = datetime.utcnow()
    
    if not user_url_ids:
        return {
            "total_clicks": 0,
            "unique_ips": 0,
            "total_links": 0,
            "countries": {},
            "devices": {},
            "browsers": {},
            "cities": {},
            "operating_systems": {},
            "recent_clicks": [],
            "hourly_stats": [],
            "daily_stats": [],
            "period_stats": [],
            "device_stats": [],
            "os_stats": [],
            "filter": {
                "url_id": url_id,
                "start_date": start_date,
                "end_date": end_date,
                "selected_date": selected_date
            },
            "generated_at": now.isoformat()
        }
    
    from sqlmodel import select
    from app.models.analytics import ClickEvent
    
    base_query = select(ClickEvent).where(ClickEvent.url_id.in_(user_url_ids))
    
    if url_id:
        base_query = base_query.where(ClickEvent.url_id == url_id)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
    
    events = session.exec(base_query).all()
    
    stats = calculate_stats(
        session=session,
        events=events,
        url_ids=user_url_ids,
        selected_date=selected_date,
        start_date=start_dt,
        end_date=end_dt,
        limit_recent_clicks=10,
        is_admin=False
    )
    
    stats.update({
        "filter": {
            "url_id": url_id,
            "start_date": start_date,
            "end_date": end_date,
            "selected_date": selected_date
        },
        "generated_at": now.isoformat()
    })
    
    return stats

@router.get("/stats/export")
async def export_stats(
    response: Response,
    session: SessionDep,
    user_data: dict = Depends(get_current_user),
    format: str = "json",
    url_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    selected_date: Optional[str] = None
):
    user_id = user_data.get("id")
    token = user_data.get("token")
    
    user_url_ids = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL_SERVICE_URL}/my",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get user URLs")
            
            user_urls_response = response.json()
            user_urls = user_urls_response.get("urls", [])
            user_url_ids = [url["id"] for url in user_urls]
            
            if url_id and url_id not in user_url_ids:
                url_id = None
    except Exception:
        pass
    
    if not user_url_ids:
        if format == "json":
            return {"error": "No URLs found for user"}
        else:
            response.media_type = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=stats.csv"
            return "error,No URLs found for user"
    
    from sqlmodel import select
    from app.models.analytics import ClickEvent
    
    base_query = select(ClickEvent).where(ClickEvent.url_id.in_(user_url_ids))
    
    if url_id:
        base_query = base_query.where(ClickEvent.url_id == url_id)
    
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    events = session.exec(base_query).all()
    
    stats = calculate_stats(
        session=session,
        events=events,
        url_ids=user_url_ids,
        selected_date=selected_date,
        start_date=start_dt,
        end_date=end_dt,
        limit_recent_clicks=10,
        is_admin=False
    )
    
    if format == "json":
        response.media_type = "application/json"
        response.headers["Content-Disposition"] = "attachment; filename=stats.json"
        return export_stats_to_json(stats)
    else:
        response.media_type = "text/csv"
        response.headers["Content-Disposition"] = "attachment; filename=stats.csv"
        return export_stats_to_csv(stats)

@router.get("/clicks")
async def get_raw_clicks(
    session: SessionDep,
    user_data: dict = Depends(get_current_user),
    url_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    user_id = user_data.get("id")
    token = user_data.get("token")
    
    user_url_ids = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL_SERVICE_URL}/my",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get user URLs")
            
            user_urls_response = response.json()
            user_urls = user_urls_response.get("urls", [])
            user_url_ids = [url["id"] for url in user_urls]
            
            if url_id and url_id not in user_url_ids:
                url_id = None
    except Exception:
        pass
    
    if not user_url_ids:
        return {"clicks": [], "total": 0, "limit": limit, "offset": offset}
    
    from sqlmodel import select
    from app.models.analytics import ClickEvent
    
    base_query = select(ClickEvent).where(ClickEvent.url_id.in_(user_url_ids))
    
    if url_id:
        base_query = base_query.where(ClickEvent.url_id == url_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    total_query = base_query
    total_count = len(session.exec(total_query).all())
    
    events = session.exec(
        base_query.order_by(ClickEvent.clicked_at.desc()).limit(limit).offset(offset)
    ).all()
    
    clicks = [
        {
            "id": event.id,
            "url_id": event.url_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "referer": event.referer,
            "country": event.country,
            "city": event.city,
            "device_type": event.device_type,
            "browser": event.browser,
            "os": event.os,
            "clicked_at": event.clicked_at.isoformat()
        }
        for event in events
    ]
    
    return {
        "clicks": clicks,
        "total": total_count,
        "limit": limit,
        "offset": offset
    }

@router.get("/clicks/export")
async def export_raw_clicks(
    response: Response,
    session: SessionDep,
    user_data: dict = Depends(get_current_user),
    format: str = "json",
    url_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    user_id = user_data.get("id")
    token = user_data.get("token")
    
    user_url_ids = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL_SERVICE_URL}/my",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get user URLs")
            
            user_urls_response = response.json()
            user_urls = user_urls_response.get("urls", [])
            user_url_ids = [url["id"] for url in user_urls]
            
            if url_id and url_id not in user_url_ids:
                url_id = None
    except Exception:
        pass
    
    if not user_url_ids:
        if format == "json":
            return {"error": "No URLs found for user"}
        else:
            response.media_type = "text/csv"
            response.headers["Content-Disposition"] = "attachment; filename=clicks.csv"
            return "error,No URLs found for user"
    
    from sqlmodel import select
    from app.models.analytics import ClickEvent
    
    base_query = select(ClickEvent).where(ClickEvent.url_id.in_(user_url_ids))
    
    if url_id:
        base_query = base_query.where(ClickEvent.url_id == url_id)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            base_query = base_query.where(ClickEvent.clicked_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    events = session.exec(base_query.order_by(ClickEvent.clicked_at.desc())).all()
    
    if format == "json":
        response.media_type = "application/json"
        response.headers["Content-Disposition"] = "attachment; filename=clicks.json"
        return export_clicks_to_json(events)
    else:
        response.media_type = "text/csv"
        response.headers["Content-Disposition"] = "attachment; filename=clicks.csv"
        return export_clicks_to_csv(events)

@router.get("/my/clicks/url/{url_id}")
async def get_my_url_clicks_count(
    url_id: int,
    session: SessionDep,
    user_data: dict = Depends(get_current_user)
):
    user_id = user_data.get("id")
    token = user_data.get("token")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{URL_SERVICE_URL}/my?skip=0&limit=1000",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get user URLs")
            
            user_urls_response = response.json()
            user_urls = user_urls_response.get("urls", [])
            user_url_ids = [url["id"] for url in user_urls]
            
            if url_id not in user_url_ids:
                raise HTTPException(status_code=404, detail="URL not found or access denied")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to verify URL ownership")
    from sqlmodel import select, func
    from app.models.analytics import ClickEvent
    
    count_query = select(func.count(ClickEvent.id)).where(ClickEvent.url_id == url_id)
    total_clicks = session.exec(count_query).first()
    return {
        "url_id": url_id,
        "total_clicks": total_clicks or 0
    }
