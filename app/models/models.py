import datetime
import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    type = Column(String)  # 'hockey', 'oscar', 'all'
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    error = Column(String, nullable=True)

    results_hockey = relationship("HockeyData", back_populates="job")
    results_oscar = relationship("OscarData", back_populates="job")


class HockeyData(Base):
    __tablename__ = "hockey_data"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    team_name = Column(String)
    year = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    ot_losses = Column(Integer, nullable=True)
    win_pct = Column(Float)
    goals_for = Column(Integer)
    goals_against = Column(Integer)
    goal_diff = Column(Integer)

    job = relationship("Job", back_populates="results_hockey")

    __table_args__ = (UniqueConstraint("team_name", "year", name="_team_year_uc"),)


class OscarData(Base):
    __tablename__ = "oscar_data"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    year = Column(Integer)
    title = Column(String)
    nominations = Column(Integer)
    awards = Column(Integer)
    best_picture = Column(Boolean)

    job = relationship("Job", back_populates="results_oscar")

    __table_args__ = (UniqueConstraint("title", "year", name="_title_year_uc"),)
