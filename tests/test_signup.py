import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db_configuration import get_db, Base
from app.main import app

# Set up the test client
client = TestClient(app)

# Set up the test database
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    DATABASE_URL,  # Database URL
    connect_args={"check_same_thread": False},  # Required for SQLite
    pool_pre_ping=True,  # Option to ensure the connection is alive before using
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to override the get_db dependency in the main app
def override_get_db():
    database = TestingSessionLocal()
    yield database
    database.close()


app.dependency_overrides[get_db] = override_get_db


# Setup and teardown for the test database
@pytest.fixture(scope="module")
def setup_database():
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables in the test database after tests are done
    Base.metadata.drop_all(bind=engine)


@pytest.mark.usefixtures("setup_database")
class TestGraphQL:
    def test_graphql_query(self):
        query = """
        query {
            users {
                id
                name
            }
        }
        """
        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        assert "data" in response.json()
        # Assuming there are users in the test database
        assert len(response.json()["data"]["users"]) > 0

    def test_graphql_mutation(self):
        mutation = """
        mutation {
            createUser(name: "Test User") {
                id
                name
            }
        }
        """
        response = client.post("/graphql", json={"query": mutation})
        assert response.status_code == 200
        assert response.json()["data"]["createUser"]["name"] == "Test User"

    def test_graphql_user_not_found(self):
        query = """
        query {
            user(id: 999) {
                id
                name
            }
        }
        """
        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        assert "errors" in response.json()
        assert response.json()["errors"][0]["message"] == "User not found"
