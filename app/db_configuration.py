import os
from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv("../.env")

# Fetch the database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Use SQLite for testing if DATABASE_URL is not set
TEMP_DATABASE_URL="sqlite:///./test.db"
SQLALCHEMY_DATABASE_URL = TEMP_DATABASE_URL

# Error handling if the environment variable is not found
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment")

# Create the SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,  # Database URL
    connect_args={"check_same_thread": False},  # Required for SQLite
    pool_pre_ping=True,  # Option to ensure the connection is alive before using
)

# Create a session factory and configure scoped session
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for models
Base = declarative_base()

# Attach a convenient query property to the Base class for ORM queries
Base.query = db_session.query_property()

# Dependency for FastAPI to get the database session in routes
def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()

# Function to set up the database (if needed)
def init_db():
    db = db_session()
    try:
        Base.metadata.create_all(bind=db.bind)  # Create all tables
    finally:
        db.close()
