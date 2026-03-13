from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    name: str
    weekly_steps: int = 0
    workouts_completed: int = 0
    streak: int = 0
    total_points: float = 0

    class Config:
        from_attributes = True


class LeaderboardOut(BaseModel):
    entries: list[LeaderboardEntry]
    total: int = 0


class MyRank(BaseModel):
    rank: int | None = None
    total_points: float = 0
    weekly_steps: int = 0
    workouts_completed: int = 0
    streak: int = 0
    is_flagged: bool = False
    message: str | None = None
