from pathlib import Path
import pytest
import os
import json
import mimetypes
import logging

# Configure the logger
logger = logging.getLogger(__name__)


# Class for Role id optional
class Role:
    def __init__(self, name, description):
        self.id = None
        self.name = name
        self.description = description


# Class for User
class User:
    def __init__(self, username, email, role, password):
        self.id = None
        self.username = username
        self.email = email
        self.role = role
        self.password = password
        self.profile = None
        self.access_token = None


# Class for UserProfile
class UserProfile:
    def __init__(self, user, first_name, last_name, bio, profile_photo):
        self.user = user
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.profile_photo = profile_photo


# Class for Post
class Post:
    def __init__(self, user, content, likes, visibility, post_type, medias):
        self.id = None
        self.user = user
        self.content = content
        self.likes = likes
        self.visibility = visibility
        self.post_type = post_type
        self.medias = medias


# Class for Media
class Media:
    def __init__(self, file_url, media_type):
        self.file_url = file_url
        self.media_type = media_type


ROLE_1 = Role("Admin", "Administrator role with full permissions")
ROLE_2 = Role("User", "User role with limited permissions")

USER_1 = User("test", "test@test.com", ROLE_1, "password")
USER_2 = User("test2", "test2@test.com", ROLE_2, "password123")

USER_PROFILE_1 = UserProfile(
    USER_1,
    "Test",
    "User",
    "This is a test user",
    "tests/imgs/test_profile_picture.jpeg",
)
USER_PROFILE_2 = UserProfile(
    USER_2,
    "Test2",
    "User2",
    "This is a test user 2",
    "tests/imgs/test_profile_picture_2.jpeg",
)

MEDIA_1 = Media("tests/imgs/test_post_1.jpeg", "image/jpeg")
MEDIA_2 = Media("tests/imgs/test_post_2.jpg", "image/jpeg")
MEDIA_3 = Media("tests/imgs/test_post_3.jpg", "image/jpeg")

POST_1 = Post(
    USER_1, "This is a test post content.", 0, "PUBLIC", "POST", [MEDIA_1, MEDIA_2]
)
POST_2 = Post(USER_2, "This is a test post content 2.", 0, "PRIVATE", "POST", [MEDIA_3])


# ROLE_ID = None
# ROLE_NAME = "Admin"
# ROLE_DESCRIPTION = "Administrator role with full permissions"

# USER_ID = None
# USER_NAME = "test"
# USER_EMAIL = "test@test.com"
# USER_PASSWORD = "password"
# ACCESS_TOKEN = None

# NEW_FIRST_NAME = "NewFirstName"
# NEW_LAST_NAME = "NewLastName"
# NEW_BIO = "NewBio"
# USER_PROFILE_PICTURE = "tests/imgs/test_profile_picture.jpeg"

# TEST_CONTENT = "This is a test post content."
# TEST_VISIBILITY = "PUBLIC"
# TEST_POST_TYPE = "POST"
# TEST_MEDIA_FILES = []
# POST_ID = None

# TEST_MEDIA_FILES = [
#     "tests/imgs/test_post_1.jpeg",
#     "tests/imgs/test_post_2.jpg",
#     "tests/imgs/test_post_3.jpg",
# ]


# Test Role Model
@pytest.mark.usefixtures("client")
class TestRole:
    global ROLE_1
    global ROLE_2

    # Test create role mutation
    @pytest.mark.parametrize(
        "ROLE",
        [
            (ROLE_1),
            (ROLE_2),
        ],
    )
    def test_create_role(self, client, ROLE):
        mutation = f"""
        mutation {{
            createRole(name: "{ROLE.name}", description: "{ROLE.description}") {{
                ok,
                roleId
            }}
        }}
        """
        # Send the request
        response = client.post("/graphql/", json={"query": mutation})
        # Check the response
        assert response.status_code == 200
        assert response.json()["data"]["createRole"]["ok"] is True
        assert response.json()["data"]["createRole"]["roleId"] > 0
        ROLE.id = response.json()["data"]["createRole"]["roleId"]
        logger.info(ROLE.__dict__)

    # Test query role by id
    @pytest.mark.parametrize(
        "ROLE",
        [
            (ROLE_1),
            (ROLE_2),
        ],
    )
    def test_query_role(self, client, ROLE):
        logger.info(f"Querying Role: {ROLE.__dict__}")

        # Ensure that ROLE.id exists and is valid
        assert ROLE.id is not None, "ROLE.id is not set from the create role mutation"

        query = f"""
        query {{
            roleById(roleId: {ROLE.id}) {{
                id,
                name,
                description
            }}
        }}
        """
        # Send the request
        response = client.post("/graphql/", json={"query": query})
        # Check the response
        assert response.status_code == 200
        assert int(response.json()["data"]["roleById"]["id"]) == ROLE.id
        assert response.json()["data"]["roleById"]["name"] == ROLE.name
        assert response.json()["data"]["roleById"]["description"] == ROLE.description


# Test User Model
@pytest.mark.usefixtures("client")
class TestUser:
    global USER_1
    global USER_2

    # Test create user mutation
    @pytest.mark.parametrize(
        "USER",
        [
            (USER_1),
            (USER_2),
        ],
    )
    def test_create_user(self, client, USER):
        mutation = f"""
        mutation {{
            createUser(username: "{USER.username}", email: "{USER.email}", roleId: {USER.role.id}, password: "{USER.password}") {{
                ok,
                userId
            }}
        }}
        """
        # Send the request
        response = client.post("/graphql/", json={"query": mutation})
        # Check the response
        assert response.status_code == 200
        assert response.json()["data"]["createUser"]["ok"] is True
        USER.id = response.json()["data"]["createUser"]["userId"]

    # Test query user by id
    @pytest.mark.parametrize(
        "USER",
        [
            (USER_1),
            (USER_2),
        ],
    )
    def test_login(self, client, USER):
        mutation = f"""
        mutation {{
            login(username: "{USER.username}", password: "{USER.password}") {{
                ok,
                accessToken
            }}
        }}
        """
        # Send the request
        response = client.post("/graphql/", json={"query": mutation})
        # Check the response
        assert response.status_code == 200
        assert response.json()["data"]["login"]["ok"] is True
        USER.access_token = response.json()["data"]["login"]["accessToken"]

    # Test query user by id
    @pytest.mark.parametrize(
        "USER",
        [
            (USER_1),
            (USER_2),
        ],
    )
    def test_query_user(self, client, USER):
        query = f"""
        query {{
            userById(userId: {USER.id}) {{
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
        # Send the request
        response = client.post("/graphql/", json={"query": query})
        # Check the response
        assert response.status_code == 200
        assert int(response.json()["data"]["userById"]["id"]) == USER.id
        assert response.json()["data"]["userById"]["username"] == USER.username
        assert response.json()["data"]["userById"]["email"] == USER.email
        assert (
            response.json()["data"]["userById"]["profile"]["firstName"] == USER.username
        )
        assert (
            response.json()["data"]["userById"]["profile"]["lastName"] == USER.username
        )
        assert response.json()["data"]["userById"]["profile"]["bio"] is None
        assert response.json()["data"]["userById"]["profile"]["profilePhoto"] is None


# Test User Profile Model
@pytest.mark.usefixtures("client")
class TestUserProfile:
    global USER_PROFILE_1
    global USER_PROFILE_2

    # Test update user profile mutation
    @pytest.mark.parametrize(
        "USER_PROFILE",
        [
            (USER_PROFILE_1),
            (USER_PROFILE_2),
        ],
    )
    def test_update_user_profile(self, client, USER_PROFILE):
        # Check if the file exists
        assert Path(USER_PROFILE.profile_photo).exists()
        # Prepare the operations data
        operations = json.dumps(
            {
                "query": """
            mutation($firstName: String, $lastName: String, $bio: String, $profilePhoto: Upload) {
                updateUserProfile(firstName: $firstName, lastName: $lastName, bio: $bio, profilePhoto: $profilePhoto) {
                    ok
                    userId
                    profilePhotoUrl
                }
            }
            """,
                "variables": {
                    "firstName": USER_PROFILE.first_name,
                    "lastName": USER_PROFILE.last_name,
                    "bio": USER_PROFILE.bio,
                    "profilePhoto": None,
                },
            }
        )
        # Prepare the map data
        map_data = json.dumps({"0": ["variables.profilePhoto"]})

        # Prepare the files data
        with open(USER_PROFILE.profile_photo, "rb") as test_image:
            files = {
                "operations": (None, operations),
                "map": (None, map_data),
                "0": (USER_PROFILE.profile_photo, test_image, "image/jpeg"),
            }

            response = client.post(
                "/graphql/",
                files=files,
                headers={"Authorization": f"Bearer {USER_PROFILE.user.access_token}"},
            )

        # Check the response
        assert response.status_code == 200
        response_data = response.json()
        logger.info(response_data)
        assert response_data["data"]["updateUserProfile"]["ok"] is True

    # Test query user profile by user id
    @pytest.mark.parametrize(
        "USER_PROFILE",
        [
            (USER_PROFILE_1),
            (USER_PROFILE_2),
        ],
    )
    def test_query_user_profile(self, client, USER_PROFILE):
        query = f"""
        query {{
            userProfile(userId: {USER_PROFILE.user.id}) {{
                firstName,
                lastName,
                bio,
                profilePhoto
            }}
        }}
        """
        # Send the request
        response = client.post("/graphql/", json={"query": query})
        # Check the response
        assert response.status_code == 200
        assert (
            response.json()["data"]["userProfile"]["firstName"]
            == USER_PROFILE.first_name
        )
        assert (
            response.json()["data"]["userProfile"]["lastName"] == USER_PROFILE.last_name
        )
        assert response.json()["data"]["userProfile"]["bio"] == USER_PROFILE.bio
        if USER_PROFILE.profile_photo is not None:
            # Check if the profile photo exists
            assert Path(response.json()["data"]["userProfile"]["profilePhoto"]).exists()
            # Optionally delete the file after the test
            os.remove(response.json()["data"]["userProfile"]["profilePhoto"])


# Test File Upload
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
        # Check if the file exists
        assert Path(file_path).exists()

        # Automatically guess the content type based on the file extension
        content_type, _ = mimetypes.guess_type(file_path)
        assert content_type is not None, "Unable to guess content type"
        # Prepare the operations data
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
        # Prepare the map data
        map_data = json.dumps({"0": ["variables.file"]})
        # Prepare the files data
        with open(file_path, "rb") as test_image:
            files = {
                "operations": (None, operations),
                "map": (None, map_data),
                "0": (file_path, test_image, content_type),
            }
            # Send the request
            response = client.post("/graphql/", files=files)
        # Check the response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["data"]["fileUpload"]["ok"] is True
        assert response_data["data"]["fileUpload"]["filename"] == os.path.basename(
            file_path
        )
        assert Path(response_data["data"]["fileUpload"]["filepath"]).exists()
        # delete the file after the test
        os.remove(response_data["data"]["fileUpload"]["filepath"])


# Test Post Model
@pytest.mark.usefixtures("client")
class TestCreatePost:
    global POST_1
    global POST_2

    # Test create post mutation
    @pytest.mark.parametrize(
        "POST",
        [
            (POST_1),
            (POST_2),
        ],
    )
    def test_create_post(self, client, POST):

        # Check if the media files exist
        for media in POST.medias:
            assert Path(media.file_url).exists()

        # Prepare the operations data
        operations = json.dumps(
            {
                "query": """
                mutation($content: String!, $visibility: String, $postType: String, $mediaFiles: [Upload]) {
                    createPost(content: $content, visibility: $visibility, postType: $postType, mediaFiles: $mediaFiles) {
                        ok
                        postId
                    }
                }
                """,
                "variables": {
                    "content": POST.content,
                    "visibility": POST.visibility,
                    "postType": POST.post_type,
                    "mediaFiles": [None] * len(POST.medias),
                },
            }
        )
        # Prepare the map data
        map_data = json.dumps(
            {str(i): [f"variables.mediaFiles.{i}"] for i in range(len(POST.medias))}
        )
        # Prepare the files data
        files = {}
        for i, media_file in enumerate(POST.medias):
            files[str(i)] = (str(media_file.file_url), open(media_file.file_url, "rb"), "image/jpeg")

        files["operations"] = (None, operations)
        files["map"] = (None, map_data)
        # Send the request
        response = client.post(
            "/graphql/",
            files=files,
            headers={"Authorization": f"Bearer {POST.user.access_token}"},
        )
        # Check the response
        assert response.status_code == 200
        response_data = response.json()
        logger.info(response_data)
        assert response_data["data"]["createPost"]["ok"] is True
        POST.id = response_data["data"]["createPost"]["postId"]

    # Test query post by id
    @pytest.mark.parametrize(
        "POST",
        [
            (POST_1),
            (POST_2),
        ],
    )
    def test_query_post(self, client, POST):
        query = f"""
        query {{
            post(postId: {POST.id}) {{
                id,
                content,
                likes,
                visibility,
                postType,
                media {{
                    fileUrl,
                    mediaType
                }}
            }}
        }}
        """
        # Send the request
        response = client.post("/graphql/", json={"query": query})
        # Check the response
        assert response.status_code == 200
        post_data = response.json()["data"]["post"]
        assert post_data["content"] == POST.content
        assert post_data["visibility"].lower() == POST.visibility.lower()
        assert post_data["postType"].lower() == POST.post_type.lower()

        # Check if media files are returned and remove if necessary
        media_files = post_data["media"]
        assert media_files is not None
        for media in media_files:
            assert Path(media["fileUrl"]).exists()  # Ensure the media file exists
            # Optionally delete the file after the test
            os.remove(media["fileUrl"])
