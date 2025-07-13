from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlmodel import select, func, Session
from app.models.analytics import ClickEvent

def calculate_stats(
    session: Session,
    events: List[ClickEvent],
    url_ids: List[int],
    selected_date: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit_recent_clicks: int = 10,
    is_admin: bool = False
) -> Dict[str, Any]:
    if not events:
        return {
            "total_clicks": 0,
            "unique_ips": 0,
            "total_links": len(url_ids) if url_ids else 0,
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
            **({"top_referrers": {}, "top_user_agents": {}, "top_ips": {}} if is_admin else {})
        }
    
    total_clicks = len(events)
    unique_ips = len(set(event.ip_address for event in events))
    unique_links = len(set(event.url_id for event in events))
    
    countries = {}
    devices = {}
    browsers = {}
    cities = {}
    operating_systems = {}
    referrers = {} if is_admin else None
    user_agents = {} if is_admin else None
    ip_counts = {} if is_admin else None
    
    hourly_clicks = [0] * 24
    daily_clicks = {}
    monthly_clicks = {}
    
    for event in events:
        if event.country and event.country != "Unknown":
            countries[event.country] = countries.get(event.country, 0) + 1
        
        if event.city and event.city != "Unknown":
            cities[event.city] = cities.get(event.city, 0) + 1
        
        if event.device_type and event.device_type != "Unknown":
            devices[event.device_type] = devices.get(event.device_type, 0) + 1
            
        if event.browser and event.browser != "Unknown":
            browsers[event.browser] = browsers.get(event.browser, 0) + 1
            
        if event.os and event.os != "Unknown":
            operating_systems[event.os] = operating_systems.get(event.os, 0) + 1
        
        if is_admin:
            if event.referer:
                referrers[event.referer] = referrers.get(event.referer, 0) + 1
                
            if event.user_agent:
                user_agents[event.user_agent] = user_agents.get(event.user_agent, 0) + 1
                
            if event.ip_address:
                ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1
        
        hour = event.clicked_at.hour
        hourly_clicks[hour] += 1
        
        day = event.clicked_at.date().isoformat()
        daily_clicks[day] = daily_clicks.get(day, 0) + 1
        
        month = event.clicked_at.strftime("%Y-%m")
        monthly_clicks[month] = monthly_clicks.get(month, 0) + 1
    
    if selected_date:
        try:
            selected_dt = datetime.fromisoformat(selected_date)
            selected_day = selected_dt.date().isoformat()
            
            day_events = [e for e in events if e.clicked_at.date().isoformat() == selected_day]
            day_hourly_clicks = [0] * 24
            
            for event in day_events:
                hour = event.clicked_at.hour
                day_hourly_clicks[hour] += 1
            
            hourly_stats = [
                {"hour": f"{i:02d}:00", "clicks": day_hourly_clicks[i]} 
                for i in range(24)
            ]
        except ValueError:
            hourly_stats = [
                {"hour": f"{i:02d}:00", "clicks": hourly_clicks[i]} 
                for i in range(24)
            ]
    else:
        hourly_stats = [
            {"hour": f"{i:02d}:00", "clicks": hourly_clicks[i]} 
            for i in range(24)
        ]
    
    recent_events = sorted(events, key=lambda x: x.clicked_at, reverse=True)[:limit_recent_clicks]
    recent_clicks = [
        {
            "id": event.id,
            "url_id": event.url_id,
            **({"ip_address": event.ip_address} if is_admin else {}),
            "country": event.country,
            "city": event.city,
            "device_type": event.device_type,
            "browser": event.browser,
            **({"os": event.os, "referer": event.referer} if is_admin else {}),
            "clicked_at": event.clicked_at.isoformat()
        }
        for event in recent_events
    ]
    
    daily_stats = [
        {"date": date, "clicks": clicks} 
        for date, clicks in sorted(daily_clicks.items())
    ][-30:]
    
    period_stats = [
        {"month": month, "clicks": clicks} 
        for month, clicks in sorted(monthly_clicks.items())
    ]
    
    device_stats = [
        {"device": device, "clicks": clicks} 
        for device, clicks in sorted(devices.items(), key=lambda x: x[1], reverse=True)
    ]
    
    os_stats = [
        {"os": os, "clicks": clicks} 
        for os, clicks in sorted(operating_systems.items(), key=lambda x: x[1], reverse=True)
    ]
    
    result = {
        "total_clicks": total_clicks,
        "unique_ips": unique_ips,
        "total_links": unique_links,
        
        "countries": dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:20 if is_admin else 10]),
        "cities": dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:20 if is_admin else 10]),
        
        "devices": dict(sorted(devices.items(), key=lambda x: x[1], reverse=True)),
        "browsers": dict(sorted(browsers.items(), key=lambda x: x[1], reverse=True)[:15 if is_admin else 10]),
        "operating_systems": dict(sorted(operating_systems.items(), key=lambda x: x[1], reverse=True)[:15 if is_admin else 10]),
        
        "hourly_stats": hourly_stats,
        "daily_stats": daily_stats,
        "period_stats": period_stats,
        "device_stats": device_stats,
        "os_stats": os_stats,
        
        "recent_clicks": recent_clicks
    }
    
    if is_admin:
        result.update({
            "top_referrers": dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:15]),
            "top_user_agents": dict(sorted(user_agents.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_ips": dict(sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        })
    
    return result
