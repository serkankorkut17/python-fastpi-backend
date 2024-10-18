from pathlib import Path
import pytest
import os
import json
import io
from app.main import app  # Import your FastAPI app
import mimetypes
import logging

# Configure the logger
logger = logging.getLogger(__name__)


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

TEST_CONTENT = "This is a test post content."
TEST_VISIBILITY = "public" # "public"  # Adjust as necessary based on your enums
TEST_POST_TYPE = "post"  # Adjust as necessary based on your enums
TEST_MEDIA_FILES = []
POST_ID = None


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
        assert response.status_code == 200
        assert response.json()["data"]["userProfile"]["firstName"] == NEW_FIRST_NAME
        assert response.json()["data"]["userProfile"]["lastName"] == NEW_LAST_NAME
        assert response.json()["data"]["userProfile"]["bio"] == NEW_BIO
        # check if the profile photo is not None exists
        assert Path(response.json()["data"]["userProfile"]["profilePhoto"]).exists()
        # delete the file after the test
        os.remove(response.json()["data"]["userProfile"]["profilePhoto"])


@pytest.mark.usefixtures("client")
class TestFileUpload:

    @pytest.mark.parametrize(
        "file_path",
        [
            ("tests/imgs/test_image.png"),
            ("tests/imgs/test_profile_picture.jpeg"),
            ("tests/files/test.txt"),
        ],
    )
    def test_file_upload(self, client, file_path):
        assert Path(file_path).exists()

        # Automatically guess the content type based on the file extension
        content_type, _ = mimetypes.guess_type(file_path)
        assert content_type is not None, "Unable to guess content type"

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
                "0": (file_path, test_image, content_type),
            }

            response = client.post("/graphql/", files=files)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["fileUpload"]["ok"] is True
        assert response_data["data"]["fileUpload"]["filename"] == os.path.basename(
            file_path
        )
        assert Path(response_data["data"]["fileUpload"]["filepath"]).exists()
        # delete the file after the test
        os.remove(response_data["data"]["fileUpload"]["filepath"])


@pytest.mark.usefixtures("client")
class TestCreatePost:

    @pytest.fixture
    def test_media_files(self):
        # Create temporary media files for testing (images/videos)
        tmp_path = Path("tests/tmp")
        tmp_path.mkdir(exist_ok=True)

        media_files = []
        for i in range(3):  # Create 3 test media files
            media_file = tmp_path / f"test_image_{i}.jpg"
            with open(media_file, "wb") as f:
                f.write(os.urandom(1024))  # 1 KB random data for testing
            media_files.append(media_file)
        return media_files

    def test_create_post(self, client, test_media_files):
        global ACCESS_TOKEN
        global POST_ID
        global TEST_CONTENT
        global TEST_VISIBILITY
        global TEST_POST_TYPE

        operations = json.dumps(
            {
                "query": """
                mutation($content: String!, $visibility: PostVisibility, $postType: PostType, $mediaFiles: [Upload]) {
                    createPost(content: $content, visibility: $visibility, postType: $postType, mediaFiles: $mediaFiles) {
                        ok
                        postId
                    }
                }
                """,
                "variables": {
                    "content": TEST_CONTENT,
                    "visibility": TEST_VISIBILITY,
                    "postType": TEST_POST_TYPE,
                    "mediaFiles": None,  # Set to None initially; will replace with files later
                },
            }
        )
        map_data = json.dumps(
            {str(i): ["variables.mediaFiles"] for i in range(len(test_media_files))}
        )

        files = {}
        for i, media_file in enumerate(test_media_files):
            files[str(i)] = (str(media_file), open(media_file, "rb"), "image/jpeg")

        files["operations"] = (None, operations)
        files["map"] = (None, map_data)

        response = client.post(
            "/graphql/",
            files=files,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )

        assert response.status_code == 200
        response_data = response.json()
        logger.info(response_data)
        assert response_data["data"]["createPost"]["ok"] is True
        POST_ID = response_data["data"]["createPost"]["postId"]

    def test_query_post(self, client):
        global POST_ID
        query = f"""
        query {{
            post(postId: {POST_ID}) {{
                id,
                content,
                likes,
                visibility,
                postType,
                mediaFiles {{
                    fileUrl,
                    mediaType
                }}
            }}
        }}
        """
        response = client.post("/graphql/", json={"query": query})
        assert response.status_code == 200
        post_data = response.json()["data"]["post"]
        assert post_data["content"] == TEST_CONTENT
        assert post_data["visibility"] == TEST_VISIBILITY
        assert post_data["postType"] == TEST_POST_TYPE

        # Check if media files are returned and remove if necessary
        media_files = post_data["mediaFiles"]
        assert media_files is not None
        for media in media_files:
            assert Path(media["fileUrl"]).exists()  # Ensure the media file exists
            # Optionally delete the file after the test
            os.remove(media["fileUrl"])

        # Clean up the post if you have a method to do so
        # For example, you might want to call a delete mutation
