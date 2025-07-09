from typing import Annotated
from sqlmodel import SQLModel, create_engine, Session
from fastapi import Depends
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

def init_db():
    from app.models.url import Url
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
