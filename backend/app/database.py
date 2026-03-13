from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
"pool_pre_ping": True,
}
if is_sqlite:
engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

if is_sqlite:
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
cursor = dbapi_connection.cursor()
cursor.execute("PRAGMA journal_mode=WAL")
cursor.execute("PRAGMA foreign_keys=ON")
cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
pass

def get_db():
db = SessionLocal()
try:
yield db
finally:
db.close()
