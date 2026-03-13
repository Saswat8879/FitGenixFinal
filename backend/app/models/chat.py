from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func
from app.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now())
    role = Column(String(20), nullable=False)  # user / assistant
    message = Column(String(5000), nullable=False)
    retrieved_context = Column(JSON, nullable=True)
