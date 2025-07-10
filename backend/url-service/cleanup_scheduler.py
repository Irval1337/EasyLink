import asyncio
import httpx
from datetime import datetime, timedelta
import os

CLEANUP_INTERVAL = 3600
URL_SERVICE_URL = os.getenv("URL_SERVICE_URL", "http://localhost:8001")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

async def cleanup_expired_urls():
    if not ADMIN_TOKEN:
        return
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{URL_SERVICE_URL}/admin/cleanup-expired",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
                timeout=30
            )
    except Exception as e:
        pass

async def run_cleanup_scheduler():
    while True:
        await cleanup_expired_urls()
        await asyncio.sleep(CLEANUP_INTERVAL)

if __name__ == "__main__":
    asyncio.run(run_cleanup_scheduler())
