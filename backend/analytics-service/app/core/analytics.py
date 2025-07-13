import re
from typing import Optional, Dict, Any
import httpx
from user_agents import parse
import os

def parse_user_agent(user_agent_string: str) -> Dict[str, Optional[str]]:
    try:
        user_agent = parse(user_agent_string)
        
        if user_agent.is_mobile:
            device_type = "Mobile"
        elif user_agent.is_tablet:
            device_type = "Tablet"
        elif user_agent.is_pc:
            device_type = "Desktop"
        else:
            device_type = "Unknown"
        
        browser_name = user_agent.browser.family or "Unknown"
        browser_version = user_agent.browser.version_string
        browser = f"{browser_name} {browser_version}".strip() if browser_version else browser_name
        
        os_name = user_agent.os.family or "Unknown"  
        os_version = user_agent.os.version_string
        os = f"{os_name} {os_version}".strip() if os_version else os_name
        
        return {
            "device_type": device_type,
            "browser": browser,
            "os": os
        }
    except Exception:
        return {
            "device_type": "Unknown",
            "browser": "Unknown",
            "os": "Unknown"
        }

async def get_location_info(ip_address: str) -> Dict[str, Optional[str]]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,city", timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country"),
                        "city": data.get("city")
                    }
    except Exception:
        pass
    
    return {
        "country": "Unknown",
        "city": "Unknown"
    }

def extract_real_ip(headers: dict) -> str:
    for header in ['x-forwarded-for', 'x-real-ip', 'cf-connecting-ip']:
        value = headers.get(header)
        if value:
            if ',' in value:
                return value.split(',')[0].strip()
            return value.strip()
    
    return headers.get('remote-addr', '127.0.0.1')
