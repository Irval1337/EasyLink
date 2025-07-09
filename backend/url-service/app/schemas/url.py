from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class UrlCreate(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = None
    expires_at: Optional[datetime] = None

class UrlResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    click_count: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UrlStats(BaseModel):
    id: int
    original_url: str
    short_code: str
    click_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None

class UrlListResponse(BaseModel):
    urls: list[UrlResponse]
    total: int
