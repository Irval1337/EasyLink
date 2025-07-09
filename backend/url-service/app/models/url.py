from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Url(SQLModel, table=True):
    __tablename__ = "urls"

    id: int = Field(primary_key=True)
    original_url: str = Field(index=True)
    short_code: str = Field(unique=True, index=True)
    user_id: int = Field(index=True)
    click_count: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
