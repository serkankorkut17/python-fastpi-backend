# python-fastpi-graphql

pip install fastapi fastapi-sqlalchemy pydantic alembic psycopg2 uvicorn python-dotenv

alembic init alembic
alembic revision --autogenerate -m "comment"
alembic upgrade head


python -m app.main
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload