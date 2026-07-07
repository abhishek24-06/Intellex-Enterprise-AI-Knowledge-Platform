from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from app.models.base import Base

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")##Load URL from .env

engine=create_engine(DATABASE_URL) #Connects PY to DB

SessionLocal=sessionmaker( #Creates DB connection
    bind=engine,
    autoflush=False,
    autocommit=False)


def get_db():#Creates a new database session for every request
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

    