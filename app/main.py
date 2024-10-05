import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from contextlib import asynccontextmanager

from app.db_configuration import get_db, init_db
from app.graphql import schema

import app.tasks.task_example as task_example


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        yield
    finally:
        await app.state.db_session.close()


# FastAPI app initialization
app = FastAPI(lifespan=lifespan)


# Add the GraphQL route to FastAPI with dependency injection for database session
app.mount(
    "/graphql",
    GraphQLApp(
        schema=schema,
        context_value=lambda request: {
            "request": request,  # Include the request object
            "db": next(get_db()),  # Include the db session
        },
        on_get=make_graphiql_handler(),
    ),
)


@app.get("/test")
async def test(a: int, b: int):
    print("a:", a)
    print("b:", b)
    task = task_example.task_example.delay(a, b)
    return JSONResponse({"Result": task.get()})
    # return {"task_id": task.id, "status": task.status}


# Example root route
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI with GraphQL for Users and Roles"}


# Entry point for running the app
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
