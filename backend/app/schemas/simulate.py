from __future__ import annotations

from pydantic import BaseModel


class SimulateFullDay(BaseModel):
    pass


class SimulateStressSpike(BaseModel):
    pass


class SimulateWeightTrend(BaseModel):
    direction: str  # loss / gain / plateau
    days: int = 30


class SimulateMealLog(BaseModel):
    pass


class SimulateWorkoutComplete(BaseModel):
    pass


class SimulationResponse(BaseModel):
    simulation_type: str
    data: dict = {}
