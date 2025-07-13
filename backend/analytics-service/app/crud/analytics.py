from sqlmodel import Session
from app.models.analytics import ClickEvent

def create_click_event(session: Session, click_data: dict) -> ClickEvent:
    click_event = ClickEvent(**click_data)
    session.add(click_event)
    session.commit()
    session.refresh(click_event)
    return click_event
