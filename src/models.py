import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from src.database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.utcnow()


class Blogger(Base):
    __tablename__ = "bloggers"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    notes = relationship("Note", back_populates="blogger", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="blogger", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id = Column(String(36), primary_key=True, default=_uuid)
    blogger_id = Column(String(36), ForeignKey("bloggers.id"), nullable=False)
    title = Column(String(500), default="")
    content = Column(Text, default="")
    source_url = Column(String(500), default="")
    metrics_json = Column(Text, default="{}")
    published_at = Column(DateTime, nullable=True)
    imported_at = Column(DateTime, default=_now)

    blogger = relationship("Blogger", back_populates="notes")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=_uuid)
    blogger_id = Column(String(36), ForeignKey("bloggers.id"), nullable=False)
    name = Column(String(200), nullable=False)
    version = Column(Integer, default=1)
    patterns_json = Column(Text, default="{}")
    example_note_ids = Column(Text, default="[]")
    total_notes_used = Column(Integer, default=0)
    status = Column(String(20), default="training")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    blogger = relationship("Blogger", back_populates="skills")
    generated_notes = relationship(
        "GeneratedNote", back_populates="skill", cascade="all, delete-orphan"
    )


class GeneratedNote(Base):
    __tablename__ = "generated_notes"

    id = Column(String(36), primary_key=True, default=_uuid)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    user_material = Column(Text, default="")
    user_requirements = Column(Text, default="")
    generated_content = Column(Text, default="")
    rating = Column(Integer, nullable=True)
    feedback_text = Column(Text, default="")
    created_at = Column(DateTime, default=_now)

    skill = relationship("Skill", back_populates="generated_notes")
