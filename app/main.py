import uvicorn
from fastapi import FastAPI
from starlette_graphene3 import GraphQLApp, make_graphiql_handler

from app.db_configuration import get_db, init_db
from app.graphql import schema


# FastAPI app initialization
app = FastAPI()


# Add the GraphQL route to FastAPI with dependency injection for database session
app.mount(
    "/graphql",
    GraphQLApp(
        schema=schema,
        context_value=lambda request: {"db": next(get_db())},
        on_get=make_graphiql_handler(),
    ),
)

@app.get("/test")
def test():
    return {"message": "This is a test route"}

# Example root route
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI with GraphQL for Users and Roles"}


# Optionally, you can add startup events to initialize the database
# @app.on_event("startup")
# async def startup_event():
#     init_db()  # Call the database initialization function


# Entry point for running the app
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
