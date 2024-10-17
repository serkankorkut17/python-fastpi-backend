from pathlib import Path
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import os
import json
import io
from app.main import app  # Import your FastAPI app


ROLE_NAME = "Admin"
ROLE_DESCRIPTION = "Administrator role with full permissions"
ROLE_ID = 1
USER_NAME = "test"
USER_EMAIL = "test@test.com"
USER_PASSWORD = "password"
ACCESS_TOKEN = None
USER_PROFILE_PICTURE = "tests/test_profile_picture.jpeg"


def test_create_role(client):
    mutation = f"""
    mutation {{
        createRole(name: "{ROLE_NAME}", description: "{ROLE_DESCRIPTION}") {{
            ok,
            roleId
        }}
    }}
    """
    response = client.post("/graphql/", json={"query": mutation})
    # check db for the created role
    assert response.status_code == 200
    assert response.json()["data"]["createRole"]["ok"] is True
    assert response.json()["data"]["createRole"]["roleId"] > 0
    global ROLE_ID
    ROLE_ID = response.json()["data"]["createRole"]["roleId"]


def test_create_user(client):
    mutation = f"""
    mutation {{
        createUser(username: "{USER_NAME}", email: "{USER_EMAIL}", roleId: {ROLE_ID}, password: "{USER_PASSWORD}") {{
            ok,
            userId
        }}
    }}
    """
    response = client.post("/graphql/", json={"query": mutation})
    assert response.status_code == 200
    assert response.json()["data"]["createUser"]["ok"] is True
    assert response.json()["data"]["createUser"]["userId"] > 0


def test_login(client):
    mutation = f"""
    mutation {{
        login(username: "{USER_NAME}", password: "{USER_PASSWORD}") {{
            ok,
            accessToken
        }}
    }}
    """
    response = client.post("/graphql/", json={"query": mutation})
    assert response.status_code == 200
    assert response.json()["data"]["login"]["ok"] is True
    assert response.json()["data"]["login"]["accessToken"] is not None
    global ACCESS_TOKEN
    ACCESS_TOKEN = response.json()["data"]["login"]["accessToken"]

def test_update_user_profile(client):
    global ACCESS_TOKEN  # Use the access token obtained from test_login

    # Define the mutation for updating first and last name
    mutation = """
    mutation UpdateUserProfile($firstName: String, $lastName: String) {
        updateUserProfile(firstName: $firstName, lastName: $lastName) {
            ok
            userId
        }
    }
    """
    
    variables = {
        "firstName": "NewFirstName",
        "lastName": "NewLastName"
    }

    # Send the mutation with the authorization token
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    response = client.post(
        "/graphql/",
        json={"query": mutation, "variables": variables},
        headers=headers
    )
    
    # Assertions to validate the update was successful
    assert response.status_code == 200
    assert response.json()["data"]["updateUserProfile"]["ok"] is True
    assert response.json()["data"]["updateUserProfile"]["userId"] is not None



import json
from pathlib import Path

def test_file_upload(client):
    # Path to the file you want to upload
    file_path = "tests/test_image.png"
    
    # Ensure the file exists before running the test
    assert Path(file_path).exists()

    # Prepare the GraphQL mutation and variables
    operations = json.dumps({
        "query": """
        mutation($file: Upload!) {
            fileUpload(file: $file) {
                ok
                filename
                filepath
            }
        }
        """,
        "variables": {"file": None}  # Placeholder for the file
    })

    # Prepare the map to indicate where the file goes
    map_data = json.dumps({
        "0": ["variables.file"]  # Map the file to the variable
    })

    # Simulate image upload using `files` for multipart/form-data
    with open(file_path, 'rb') as test_image:
        files = {
            "operations": (None, operations),
            "map": (None, map_data),
            "0": (file_path, test_image, "image/png")  # Include the file directly
        }

        # Send the request
        response = client.post("/graphql/", files=files)

    # Print the response data for debugging
    print("Response:", response.json())

    # Assert that the request was successful and the file was uploaded
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["data"]["fileUpload"]["ok"] is True
    assert response_data["data"]["fileUpload"]["filename"] == "test_image.png"