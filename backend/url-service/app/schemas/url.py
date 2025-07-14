from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class UrlCreate(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    password: Optional[str] = None
    remaining_clicks: Optional[int] = None

class UrlUpdate(BaseModel):
    original_url: Optional[HttpUrl] = None
    password: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    remaining_clicks: Optional[int] = None

class UrlResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    user_id: Optional[int] = None
    is_active: bool
    has_password: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    remaining_clicks: Optional[int] = None

    class Config:
        from_attributes = True

class UrlListResponse(BaseModel):
    urls: list[UrlResponse]
    total: int
