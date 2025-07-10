from fastapi import APIRouter, Depends
from app.database import SessionDep
from app.crud.url import check_and_deactivate_expired_urls
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/cleanup-expired")
async def cleanup_expired_urls(
    session: SessionDep,
    current_user: dict = Depends(get_current_user)
):
    count = check_and_deactivate_expired_urls(session)
    return {"message": f"Deactivated {count} URLs"}
