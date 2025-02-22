# Description: Main file for FastAPI app with GraphQL
import asyncio
import uvicorn
import socket
import json
import os
from fastapi import FastAPI, Request, UploadFile, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from pathlib import Path

# Custom imports
from app.db_configuration import get_db, init_db
from app.graphql import schema
from app.chat_server import chat_router


# Lifespan context manager for database session
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        """FastAPI başlatıldığında UDP server başlasın"""
        # app.state.db_session = get_db()  # Get a new session
        yield
    finally:
        pass
        # app.state.db_session.close()  # Close the session
        # await app.state.db_session.close()


# FastAPI app initialization
app = FastAPI(lifespan=lifespan)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Route for the chat server
app.include_router(chat_router)


# Favicon route
@app.get("/favicon.ico")
async def favicon():
    favicon_path = Path("static/favicon.png")
    return FileResponse(favicon_path, media_type="image/png")


# Upload file route
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    # Create the uploads directory if it doesn't exist
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(
        parents=True, exist_ok=True
    )
    try:
        file_location = UPLOAD_DIR / file.filename
        # Save the file with a unique name to avoid collisions
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return {"filename": file.filename, "filepath": str(file_location)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# Add the GraphQL route to FastAPI with dependency injection for database session
# def graphql_context(request: Request, db: callable = Depends(get_db)):
#     return {
#         "request": request,
#         "db": db,
#     }


app.mount(
    "/graphql",
    GraphQLApp(
        schema=schema,
        # context_value=graphql_context,  # Include the request object and db session
        context_value=lambda request: {
            "request": request,  # Include the request object
            "db": next(get_db()),  # Include the db session
        },
        on_get=make_graphiql_handler(),  # Enable GraphiQL on GET requests
    ),
)

# CELERY EXAMPLE ROUTE
# @app.get("/test")
# async def test(a: int, b: int):
#     print("a:", a)
#     print("b:", b)
#     task = cw.task_example.delay(a, b)
#     return JSONResponse(
#         {"Result": task.get(), "Task ID": task.id, "Task Status": task.status}
#     )


# Root route
@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI app with GraphQL!"}


def get_local_ip():
    try:
        # Creates a UDP socket and connects to an external address (no data is sent)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google's public DNS
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"


def main():
    local_ip = get_local_ip()
    print(f"Uvicorn running on Your Local IP Address: {local_ip}:8000")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        reload=True,
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )
    # uvicorn.run("run:app", host="0.0.0.0", reload=True, port=8000, workers=1)


if __name__ == "__main__":
    main()
