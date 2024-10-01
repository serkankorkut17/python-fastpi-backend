# python-fastpi-graphql

uvicorn main:app --reload

pip install fastapi fastapi-sqlalchemy pydantic alembic psycopg2 uvicorn python-dotenv

alembic init alembic
alembic revision --autogenerate -m "comment"
alembic upgrade head