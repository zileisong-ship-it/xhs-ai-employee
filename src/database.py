from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from src.config import load_config

Base = declarative_base()
engine = None
SessionLocal = None


def init_db():
    global engine, SessionLocal
    config = load_config()
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), config["database"]["path"]
    )
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return SessionLocal


def get_session():
    if SessionLocal is None:
        init_db()
    return SessionLocal()
