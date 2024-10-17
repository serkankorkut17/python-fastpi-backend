import pytest
import os
import json

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
#         response = client.post(
#             "/graphql/",  # Your actual GraphQL endpoint
#             data={
#                 "operations": json.dumps({
#                     "query": """
#                     mutation($file: Upload!) {
#                         myUpload(file: $file) {
#                             ok
#                         }
#                     }
#                     """,
#                     "variables": {"file": None}  # File will be inserted here via map
#                 }),
#                 "map": json.dumps({
#                     "0": ["variables.file"]  # The file will be mapped to this variable
#                 }),
#             },
#             files={
#                 "0": ("test_image.png", test_image, "image/png"),  # Image file mapped to "0"
#             },
#         )
    
#     print("Response:", response.json())

#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["data"]["myUpload"]["ok"] is True


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
