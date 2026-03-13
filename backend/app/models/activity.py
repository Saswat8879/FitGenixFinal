from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func
from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    type = Column(String(50), nullable=False)  # steps / workout / sleep / heart_rate
    data_json = Column(JSON)
    source = Column(String(20), default="manual")  # google_fit / manual / mock
