import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from fastapi.testclient import TestClient
from app.main import app
from app.db_configuration import get_db, Base

# Use an SQLite database in memory for testing
DATABASE_URL = "sqlite:///tests/test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def override_get_db():
#     db = TestingSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)  # Create tables before tests
    yield
    Base.metadata.drop_all(bind=engine)  # Drop tables after tests


@pytest.fixture(scope="module")
def client():
    # app.dependency_overrides[get_db] = override_get_db  # Apply the dependency override
    with TestClient(app) as client:
        yield client  # Provide the client for tests
