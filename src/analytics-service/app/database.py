from sqlmodel import create_engine, SQLModel, Session
from typing import Annotated
from fastapi import Depends
import logging

from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    logger.info("Initializing Analytics service database")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Analytics service database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating Analytics service database tables: {e}")
        raise

def get_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise

SessionDep = Annotated[Session, Depends(get_session)]
