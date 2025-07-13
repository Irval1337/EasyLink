import json
import csv
from io import StringIO
from typing import List, Dict, Any
from app.models.analytics import ClickEvent

def export_stats_to_json(stats: Dict[str, Any]) -> str:
    return json.dumps(stats, default=str, indent=2)

def export_stats_to_csv(stats: Dict[str, Any]) -> str:
    output = StringIO()
    
    output.write("metric,value\n")
    output.write(f"total_clicks,{stats.get('total_clicks', 0)}\n")
    output.write(f"unique_ips,{stats.get('unique_ips', 0)}\n")
    output.write(f"total_links,{stats.get('total_links', 0)}\n")
    
    if stats.get('countries'):
        output.write("\ncountry,clicks\n")
        for country, clicks in stats['countries'].items():
            output.write(f"{country},{clicks}\n")
    
    if stats.get('devices'):
        output.write("\ndevice,clicks\n")
        for device, clicks in stats['devices'].items():
            output.write(f"{device},{clicks}\n")
    
    if stats.get('browsers'):
        output.write("\nbrowser,clicks\n")
        for browser, clicks in stats['browsers'].items():
            output.write(f"{browser},{clicks}\n")
    
    return output.getvalue()

def export_clicks_to_json(events: List[ClickEvent]) -> str:
    data = [
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
    return json.dumps(data, default=str, indent=2)

def export_clicks_to_csv(events: List[ClickEvent]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "id", "url_id", "ip_address", "user_agent", "referer", 
        "country", "city", "device_type", "browser", "os", "clicked_at"
    ])
    
    for event in events:
        writer.writerow([
            event.id,
            event.url_id,
            event.ip_address,
            event.user_agent,
            event.referer,
            event.country,
            event.city,
            event.device_type,
            event.browser,
            event.os,
            event.clicked_at.isoformat()
        ])
    
    return output.getvalue()
