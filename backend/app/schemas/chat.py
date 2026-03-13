from pydantic import BaseModel
from datetime import datetime


class ChatQuery(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    retrieved_sources: list[str] = []
    disclaimer: str | None = None


class ChatMessageOut(BaseModel):
    id: int
    timestamp: datetime
    role: str
    message: str

    class Config:
        from_attributes = True
