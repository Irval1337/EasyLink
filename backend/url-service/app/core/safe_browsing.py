import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse
import httpx
from app.config import GOOGLE_SAFE_BROWSING_API_KEY, SAFE_BROWSING_ENABLED

logger = logging.getLogger(__name__)

class SafeBrowsingService:
    def __init__(self):
        self.api_key = GOOGLE_SAFE_BROWSING_API_KEY
        self.enabled = SAFE_BROWSING_ENABLED and bool(self.api_key)
        self.base_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        
    async def check_url_safety(self, url: str) -> Dict[str, any]:
        if not self.enabled:
            return {
                "is_safe": True,
                "threats": [],
                "details": "Safe Browsing check disabled"
            }
        
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = f"https://{url}"
            payload = {
                "client": {
                    "clientId": "easylink-url-shortener",
                    "clientVersion": "1.0"
                },
                "threatInfo": {
                    "threatTypes": [
                        "MALWARE",
                        "SOCIAL_ENGINEERING",
                        "UNWANTED_SOFTWARE",
                        "POTENTIALLY_HARMFUL_APPLICATION"
                    ],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "matches" in result and result["matches"]:
                        threats = [match["threatType"] for match in result["matches"]]
                        return {
                            "is_safe": False,
                            "threats": threats,
                            "details": f"URL flagged with threats: {', '.join(threats)}"
                        }
                    else:
                        return {
                            "is_safe": True,
                            "threats": [],
                            "details": "URL passed safety check"
                        }
                else:
                    logger.error(f"Safe Browsing API error: {response.status_code} - {response.text}")
                    return {
                        "is_safe": True,
                        "threats": [],
                        "details": f"Safety check failed (API error: {response.status_code})"
                    }
                    
        except Exception as e:
            logger.error(f"Error checking URL safety: {str(e)}")
            return {
                "is_safe": True,
                "threats": [],
                "details": f"Safety check failed (error: {str(e)})"
            }
    
    def get_threat_description(self, threat_type: str) -> str:
        descriptions = {
            "MALWARE": "Malicious software that can harm your device",
            "SOCIAL_ENGINEERING": "Deceptive content designed to steal personal information",
            "UNWANTED_SOFTWARE": "Software that may be unwanted or harmful",
            "POTENTIALLY_HARMFUL_APPLICATION": "Application that may pose security risks"
        }
        return descriptions.get(threat_type, "Unknown threat type")

safe_browsing_service = SafeBrowsingService()
