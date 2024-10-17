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


# def test_file_upload(client):
#     # Path to the file you want to upload
#     file_path = "tests/test_image.png"

#     # Simulate image upload
#     with open(file_path, 'rb') as test_image:
#         # Prepare the GraphQL mutation and variables
#         operations = json.dumps({
#             "query": """
#             mutation($file: Upload!) {
#                 myUpload(file: $file) {
#                     ok
#                 }
#             }
#             """,
#             "variables": {"file": None}  # Placeholder for the file
#         })

#         # Prepare the map to indicate where the file goes
#         map_data = json.dumps({
#             "0": ["variables.file"]  # Map the file to the variable
#         })

#         # Prepare the multipart/form-data request
#         data = {
#             "operations": operations,
#             "map": map_data,
#             "0": (file_path, test_image, "image/png")  # Include the file directly
#         }

#         # Correctly define headers as a dictionary
#         headers = {"Content-Type": "multipart/form-data"}

#         # Send the request
#         response = client.post("/graphql/", data=data , headers=headers)

#     print("Response:", response.json())

#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["data"]["myUpload"]["ok"] is True


# @pytest.mark.asyncio
# async def test_file_upload_async(client):
#     # Prepare a fake file to upload
#     file_content = b'This is a test file.'
#     fake_file = io.BytesIO(file_content)
#     fake_file.name = 'test_file.txt'  # Set the name of the file

#     # Prepare the GraphQL mutation for file upload
#     query = '''
#         mutation($file: Upload!) {
#             fileUpload(file: $file) {
#                 ok
#             }
#         }
#     '''
    
#     # Use a multipart request to upload the file
#     response = client.post(
#         '/graphql',  # Replace with your GraphQL endpoint
#         data={
#             'operations': '{"query": "%s", "variables": {"file": null}}' % query,
#             'map': '{"0": ["variables.file"]}',
#             '0': (fake_file.name, fake_file, 'text/plain'),  # Add the fake file here
#         },
#     )

#     print("Response:", response.json())

#     # Check if the response is successful
#     assert response.status_code == 200
#     result = response.json()
#     assert result['data']['fileUpload']['ok'] is True


# def test_update_user_profile(client):
#     headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

#     # GraphQL mutation string
#     mutation = """
#     mutation UpdateUserProfile($firstName: String, $lastName: String, $bio: String, $profilePhoto: Upload) {
#         updateUserProfile(firstName: $firstName, lastName: $lastName, bio: $bio, profilePhoto: $profilePhoto) {
#             ok
#             userId
#         }
#     }
#     """

#     variables = {
#         "firstName": "Jane",
#         "lastName": "Doe",
#         "bio": "Updated bio!",
#         "profilePhoto": None,
#     }

#     operations = json.dumps({"query": mutation, "variables": variables})

#     map = json.dumps({"0": ["variables.profilePhoto"]})
#     file = open(USER_PROFILE_PICTURE, "rb")

#     response = client.post(
#         "/graphql",
#         data={
#             "operations": operations,
#             "map": map,
#         },
#         files={"0": file},
#         headers=headers,
#     )

#     # Simulate a profile picture upload
#     # with open(USER_PROFILE_PICTURE, "rb") as img:
#     #     response = client.post(
#     #         "/graphql",
#     #         data={
#     #             "operations": json.dumps(operations),
#     #             "map": json.dumps(map_),
#     #             "0": img,  # Actual file to be uploaded
#     #         },
#     #         headers=headers  # Ensure the headers include Authorization
#     #     )

#     print("Response:", response.json())

#     # Check the response
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["data"]["updateUserProfile"]["ok"] is True
#     assert response_data["data"]["updateUserProfile"]["userId"] is not None


# def test_query_users(client):
#     query = """
#     query {
#         users {
#             id
#             name
#         }
#     }
#     """
#     response = client.post("/graphql", json={"query": query})
#     assert response.status_code == 200
#     assert "data" in response.json()
#     assert len(response.json()["data"]["users"]) > 0  # Adjust according to your schema


# @pytest.mark.asyncio
# async def test_file_upload(setup_db):  # Ensure setup_db is executed before the test
#     # Prepare the file to upload
#     file_path = "tests/test_file.txt"
#     with open(file_path, "w") as f:
#         f.write("This is a test file.")

#     # Prepare the multipart data
#     files = {
#         "file": ("test_file.txt", open(file_path, "rb"), "text/plain"),
#     }

#     # Construct the GraphQL mutation query
#     mutation = """
#     mutation uploadFile($file: Upload!) {
#         uploadFile(file: $file) {
#             ok
#             filename
#             filepath
#         }
#     }
#     """

#     # Create a dictionary for the operations
#     operations = {
#         "query": mutation,
#         "variables": {"file": None},
#     }

#     # Map the file input
#     map_ = {
#         "0": ["variables.file"],
#     }

#     # Use AsyncClient for async operations
#     async with AsyncClient(app=app, base_url="http://test") as async_client:
#         # Send the request
#         response = await async_client.post(
#             "/graphql/",
#             data={
#                 "operations": json.dumps(operations),
#                 "map": json.dumps(map_),
#                 **files,  # Include the files in the request
#             },
#         )

#     print("Response:", response.json())
#     # Check response status code
#     assert response.status_code == 200

#     # Check if the mutation was successful
#     response_data = response.json()
#     assert response_data["data"]["uploadFile"]["ok"] is True
#     assert response_data["data"]["uploadFile"]["filename"] == "test_file.txt"

#     # Clean up the test file
#     os.remove(file_path)
