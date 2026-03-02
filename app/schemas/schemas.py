from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class JobBase(BaseModel):
    type: str


class JobCreate(JobBase):
    pass


class JobStatus(JobBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class HockeyDataSchema(BaseModel):
    team_name: str
    year: int
    wins: int
    losses: int
    ot_losses: Optional[int]
    win_pct: float
    goals_for: int
    goals_against: int
    goal_diff: int
    model_config = ConfigDict(from_attributes=True)


class OscarDataSchema(BaseModel):
    year: int
    title: str
    nominations: int
    awards: int
    best_picture: bool
    model_config = ConfigDict(from_attributes=True)


class JobResults(JobStatus):
    results_hockey: List[HockeyDataSchema] = []
    results_oscar: List[OscarDataSchema] = []
    model_config = ConfigDict(from_attributes=True)
