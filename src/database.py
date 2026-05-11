from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from src.config import load_config, get_env_config

Base = declarative_base()
engine = None
SessionLocal = None


def init_db():
    global engine, SessionLocal
    env_config = get_env_config()
    database_url = env_config.get("DATABASE_URL", "")

    if database_url:
        # PostgreSQL 或其它 SQLAlchemy 兼容数据库
        engine = create_engine(
            database_url, echo=False,
            pool_size=5, max_overflow=10,
            pool_pre_ping=True, pool_recycle=3600,
        )
    else:
        # SQLite 本地模式
        config = load_config()
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), config["database"]["path"]
        )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        engine = create_engine(
            f"sqlite:///{db_path}", echo=False,
            connect_args={"check_same_thread": False},
        )

    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return SessionLocal


def get_session():
    if SessionLocal is None:
        init_db()
    return SessionLocal()
