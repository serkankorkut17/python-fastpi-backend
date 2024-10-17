# Description: Main file for FastAPI app with GraphQL
import uvicorn
from fastapi import FastAPI, Request, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

# custom imports
from app.db_configuration import get_db, init_db
from app.graphql import schema
from app.utils import logger
# import app.celery_worker as cw


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        app.state.db_session = get_db()  # Get a new session
        yield
    finally:
        pass
        app.state.db_session.close()  # Close the session
        # await app.state.db_session.close()


# FastAPI app initialization
app = FastAPI(lifespan=lifespan)

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Create the uploads directory if it doesn't exist

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    try:
        file_location = UPLOAD_DIR / file.filename
        # Save the file with a unique name to avoid collisions
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return {"filename": file.filename, "filepath": str(file_location)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


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

# CELERY ROUTE
# @app.get("/test")
# async def test(a: int, b: int):
#     print("a:", a)
#     print("b:", b)
#     task = cw.task_example.delay(a, b)
#     return JSONResponse(
#         {"Result": task.get(), "Task ID": task.id, "Task Status": task.status}
#     )


# Example root route
@app.get("/")
def root():
    return {"message": "Welcome to FastAPI with GraphQL for Users and Roles"}


# Entry point for running the app
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
