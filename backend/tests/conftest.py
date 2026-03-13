"""Shared test fixtures: in-memory DB, test client, auth helpers."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.auth_utils import hash_password, create_access_token

TEST_DB_URL = "sqlite:///./test_fitgenix.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os
    try:
        if os.path.exists("./test_fitgenix.db"):
            os.remove("./test_fitgenix.db")
    except OSError:
        pass


@pytest.fixture()
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def test_user(db):
    """Create a test user and return (user, token)."""
    existing = db.query(User).filter(User.email == "test@fitgenix.com").first()
    if existing:
        token = create_access_token({"sub": str(existing.id)})
        return existing, token

    user = User(
        email="test@fitgenix.com",
        hashed_password=hash_password("testpass123"),
        name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return user, token


@pytest.fixture()
def auth_headers(test_user):
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}
