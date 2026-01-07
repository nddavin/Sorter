import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from file_processor.database import Base
from file_processor.core.dependencies import get_db
from file_processor.main import app
from file_processor.core.config import settings

# Test database setup
test_engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin_token(client):
    # Create admin user and login
    response = client.post("/api/v1/auth/register", json={
        "username": "admin",
        "email": "admin@test.com",
        "password": "adminpass",
        "roles": "admin"
    })
    if response.status_code == 200:
        response = client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "adminpass"
        })
        return response.json()["access_token"]
    return None