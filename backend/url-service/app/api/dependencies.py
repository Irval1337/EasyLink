import httpx
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.config import USERS_SERVICE_URL

security = HTTPBearer(auto_error=False)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        print("No credentials provided")
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{USERS_SERVICE_URL}/verify-token",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            print(f"Verify token response status: {response.status_code}")
            print(f"Verify token response content: {response.text}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"User data: {user_data}")
                return user_data
            return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

async def get_current_user(user_data: dict = Depends(verify_token)) -> dict:
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return {"id": user_data["user_id"]}

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    return await verify_token(credentials)
