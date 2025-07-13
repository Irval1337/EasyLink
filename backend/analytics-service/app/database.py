from sqlmodel import create_engine, SQLModel, Session
from typing import Annotated
from fastapi import Depends

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
