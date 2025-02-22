import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.db_configuration import get_db, init_db, Base
from unittest.mock import patch, MagicMock

# Use an SQLite database in memory for testing
DATABASE_URL = "sqlite:///tests/test2.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# Override the dependency to use the test database
@patch("app.db_configuration.get_db")
def override_get_db():
    db = TestingSessionLocal()
    try:
        Base.metadata.create_all(bind=engine)  # Create all tables
        yield db
    finally:
        db.close()

@patch("app.db_configuration.init_db")
def override_init_db():
    db = TestingSessionLocal()
    try:
        Base.metadata.create_all(bind=engine)  # Create all tables
    finally:
        db.close()


# Set up the database before running tests and tear it down after tests
@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)  # Create tables before tests
    yield
    # Base.metadata.drop_all(bind=engine)  # Drop tables after tests


# Create a test client for the FastAPI application
@pytest.fixture(scope="module")
def client():
    # Create tables in the test database
    # Base.metadata.create_all(bind=engine)
    # app.dependency_overrides[init_db] = override_init_db
    # app.dependency_overrides[get_db] = override_get_db  # Apply the dependency override
    # Patch `get_db` and `init_db`
    with patch("app.db_configuration.get_db", override_get_db):
        with patch("app.db_configuration.init_db", override_init_db):
            with TestClient(fastapi_app) as client:
                yield client  # Provide the client for tests


