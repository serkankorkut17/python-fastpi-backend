from pathlib import Path
import pytest
import os
import json
import io
from app.main import app  # Import your FastAPI app


ROLE_ID = None
ROLE_NAME = "Admin"
ROLE_DESCRIPTION = "Administrator role with full permissions"
USER_ID = None
USER_NAME = "test"
USER_EMAIL = "test@test.com"
USER_PASSWORD = "password"
ACCESS_TOKEN = None
NEW_FIRST_NAME = "NewFirstName"
NEW_LAST_NAME = "NewLastName"
NEW_BIO = "NewBio"
USER_PROFILE_PICTURE = "tests/imgs/test_profile_picture.jpeg"

@pytest.mark.usefixtures("client")
class TestRole:

    def test_create_role(self, client):
        global ROLE_ID
        mutation = f"""
        mutation {{
            createRole(name: "{ROLE_NAME}", description: "{ROLE_DESCRIPTION}") {{
                ok,
                roleId
            }}
        }}
        """
        response = client.post("/graphql/", json={"query": mutation})
        assert response.status_code == 200
        assert response.json()["data"]["createRole"]["ok"] is True
        assert response.json()["data"]["createRole"]["roleId"] > 0
        ROLE_ID = response.json()["data"]["createRole"]["roleId"]

    def test_query_role(self, client):
        global ROLE_ID
        query = f"""
        query {{
            roleById(roleId: {ROLE_ID}) {{
                id,
                name,
                description
            }}
        }}
        """
        response = client.post("/graphql/", json={"query": query})
        assert response.status_code == 200
        assert int(response.json()["data"]["roleById"]["id"]) == ROLE_ID
        assert response.json()["data"]["roleById"]["name"] == ROLE_NAME
        assert response.json()["data"]["roleById"]["description"] == ROLE_DESCRIPTION


@pytest.mark.usefixtures("client")
class TestUser:

    def test_create_user(self, client):
        global ROLE_ID
        global USER_ID
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
        USER_ID = response.json()["data"]["createUser"]["userId"]


    def test_login(self, client):
        global ACCESS_TOKEN
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
        ACCESS_TOKEN = response.json()["data"]["login"]["accessToken"]

    def test_query_user(self, client):
        global USER_ID
        query = f"""
        query {{
            userById(userId: {USER_ID}) {{
                id,
                username,
                email,
                profile {{
                    firstName,
                    lastName,
                    bio,
                    profilePhoto
                }}
            }}
        }}
        """
        response = client.post("/graphql/", json={"query": query})
        assert response.status_code == 200
        assert int(response.json()["data"]["userById"]["id"]) == USER_ID
        assert response.json()["data"]["userById"]["username"] == USER_NAME
        assert response.json()["data"]["userById"]["email"] == USER_EMAIL
        assert response.json()["data"]["userById"]["profile"]["firstName"] == USER_NAME
        assert response.json()["data"]["userById"]["profile"]["lastName"] == USER_NAME
        assert response.json()["data"]["userById"]["profile"]["bio"] is None
        assert response.json()["data"]["userById"]["profile"]["profilePhoto"] is None


@pytest.mark.usefixtures("client")
class TestUserProfile:

    def test_update_user_profile(self, client):
        global ACCESS_TOKEN
        global USER_ID
        global NEW_FIRST_NAME
        global NEW_LAST_NAME
        global NEW_BIO
        global USER_PROFILE_PICTURE

        assert Path(USER_PROFILE_PICTURE).exists()

        operations = json.dumps(
            {
                "query": """
            mutation($firstName: String, $lastName: String, $bio: String, $profilePhoto: Upload) {
                updateUserProfile(firstName: $firstName, lastName: $lastName, bio: $bio, profilePhoto: $profilePhoto) {
                    ok
                    userId
                }
            }
            """,
                "variables": {
                    "firstName": NEW_FIRST_NAME,
                    "lastName": NEW_LAST_NAME,
                    "bio": NEW_BIO,
                    "profilePhoto": None,
                },
            }
        )
        map_data = json.dumps({"0": ["variables.profilePhoto"]})

        with open(USER_PROFILE_PICTURE, "rb") as test_image:
            files = {
                "operations": (None, operations),
                "map": (None, map_data),
                "0": (USER_PROFILE_PICTURE, test_image, "image/jpeg"),
            }

            response = client.post(
                "/graphql/",
                files=files,
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["updateUserProfile"]["ok"] is True
        USER_ID = response_data["data"]["updateUserProfile"]["userId"]


    def test_query_user_profile(self, client):
        global USER_ID
        query = f"""
        query {{
            userProfile(userId: {USER_ID}) {{
                firstName,
                lastName,
                bio,
                profilePhoto
            }}
        }}
        """
        response = client.post("/graphql/", json={"query": query})
        print(response.json())
        assert response.status_code == 200
        assert response.json()["data"]["userProfile"]["firstName"] == NEW_FIRST_NAME
        assert response.json()["data"]["userProfile"]["lastName"] == NEW_LAST_NAME
        assert response.json()["data"]["userProfile"]["bio"] == NEW_BIO
        assert response.json()["data"]["userProfile"]["profilePhoto"] is not None


@pytest.mark.usefixtures("client")
class TestFileUpload:

    @pytest.mark.parametrize("file_path", [
        ("tests/imgs/test_image.png"),
        ("tests/imgs/test_profile_picture.jpeg"),
    ])
    def test_file_upload(self, client, file_path):
        assert Path(file_path).exists()

        operations = json.dumps(
            {
                "query": """
            mutation($file: Upload!) {
                fileUpload(file: $file) {
                    ok
                    filename
                    filepath
                }
            }
            """,
                "variables": {"file": None},
            }
        )
        map_data = json.dumps({"0": ["variables.file"]})

        with open(file_path, "rb") as test_image:
            files = {
                "operations": (None, operations),
                "map": (None, map_data),
                "0": (file_path, test_image, "image/png"),
            }

            response = client.post("/graphql/", files=files)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["fileUpload"]["ok"] is True
        assert response_data["data"]["fileUpload"]["filename"] == os.path.basename(file_path)
        assert Path(response_data["data"]["fileUpload"]["filepath"]).exists()
        # delete the file after the test
        os.remove(response_data["data"]["fileUpload"]["filepath"])


# def test_create_role(client):
#     mutation = f"""
#     mutation {{
#         createRole(name: "{ROLE_NAME}", description: "{ROLE_DESCRIPTION}") {{
#             ok,
#             roleId
#         }}
#     }}
#     """
#     response = client.post("/graphql/", json={"query": mutation})
#     # check db for the created role
#     assert response.status_code == 200
#     assert response.json()["data"]["createRole"]["ok"] is True
#     assert response.json()["data"]["createRole"]["roleId"] > 0
#     global ROLE_ID
#     ROLE_ID = response.json()["data"]["createRole"]["roleId"]


# def test_create_user(client):
#     mutation = f"""
#     mutation {{
#         createUser(username: "{USER_NAME}", email: "{USER_EMAIL}", roleId: {ROLE_ID}, password: "{USER_PASSWORD}") {{
#             ok,
#             userId
#         }}
#     }}
#     """
#     response = client.post("/graphql/", json={"query": mutation})
#     assert response.status_code == 200
#     assert response.json()["data"]["createUser"]["ok"] is True
#     assert response.json()["data"]["createUser"]["userId"] > 0


# def test_login(client):
#     mutation = f"""
#     mutation {{
#         login(username: "{USER_NAME}", password: "{USER_PASSWORD}") {{
#             ok,
#             accessToken
#         }}
#     }}
#     """
#     response = client.post("/graphql/", json={"query": mutation})
#     assert response.status_code == 200
#     assert response.json()["data"]["login"]["ok"] is True
#     assert response.json()["data"]["login"]["accessToken"] is not None
#     global ACCESS_TOKEN
#     ACCESS_TOKEN = response.json()["data"]["login"]["accessToken"]


# def test_update_user_profile(client):
#     global ACCESS_TOKEN  # Use the access token obtained from test_login
#     global NEW_FIRST_NAME  # New first name to update
#     global NEW_LAST_NAME  # New last name to update
#     global NEW_BIO  # New bio to update
#     global USER_PROFILE_PICTURE  # Path to the profile picture file

#     # Ensure the file exists before running the test
#     assert Path(USER_PROFILE_PICTURE).exists()

#     operations = json.dumps(
#         {
#             "query": """
#         mutation($firstName: String, $lastName: String, $bio: String, $profilePhoto: Upload) {
#             updateUserProfile(firstName: $firstName, lastName: $lastName, bio: $bio, profilePhoto: $profilePhoto) {
#                 ok
#                 userId
#             }
#         }
#         """,
#             "variables": {
#                 "firstName": NEW_FIRST_NAME,
#                 "lastName": NEW_LAST_NAME,
#                 "bio": NEW_BIO,
#                 "profilePhoto": None,
#             },
#         }
#     )

#     map_data = json.dumps({"0": ["variables.profilePhoto"]})

#     with open(USER_PROFILE_PICTURE, "rb") as test_image:
#         files = {
#             "operations": (None, operations),
#             "map": (None, map_data),
#             "0": (USER_PROFILE_PICTURE, test_image, "image/jpeg"),
#         }

#         response = client.post(
#             "/graphql/",
#             files=files,
#             headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
#         )

#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["data"]["updateUserProfile"]["ok"] is True
#     assert response_data["data"]["updateUserProfile"]["userId"] > 0


# def test_file_upload(client):
#     # Path to the file you want to upload
#     file_path = "tests/imgs/test_image.png"

#     # Ensure the file exists before running the test
#     assert Path(file_path).exists()

#     # Prepare the GraphQL mutation and variables
#     operations = json.dumps(
#         {
#             "query": """
#         mutation($file: Upload!) {
#             fileUpload(file: $file) {
#                 ok
#                 filename
#                 filepath
#             }
#         }
#         """,
#             "variables": {"file": None},  # Placeholder for the file
#         }
#     )

#     # Prepare the map to indicate where the file goes
#     map_data = json.dumps({"0": ["variables.file"]})  # Map the file to the variable

#     # Simulate image upload using `files` for multipart/form-data
#     with open(file_path, "rb") as test_image:
#         files = {
#             "operations": (None, operations),
#             "map": (None, map_data),
#             "0": (file_path, test_image, "image/png"),  # Include the file directly
#         }

#         # Send the request
#         response = client.post("/graphql/", files=files)

#     # Assert that the request was successful and the file was uploaded
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["data"]["fileUpload"]["ok"] is True
#     assert response_data["data"]["fileUpload"]["filename"] == "test_image.png"
