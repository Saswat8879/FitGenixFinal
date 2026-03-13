from __future__ import annotations

from pydantic import BaseModel


class LifestylePointsOut(BaseModel):
    date: str
    total: float = 0
    breakdown: dict = {}

    class Config:
        from_attributes = True


class LifestylePointsHistory(BaseModel):
    date: str
    total: float = 0
    breakdown: dict = {}
