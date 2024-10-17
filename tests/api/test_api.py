import pytest
from pathlib import Path

def test_create_upload_file_api(client):
    # Create a temporary file to upload
    test_file_path = Path("tests/test_file.txt")
    with open(test_file_path, "w") as f:
        f.write("This is a test file.")

    with open(test_file_path, "rb") as f:
        response = client.post("/uploadfile/", files={"file": ("test_file.txt", f, "text/plain")})

    # Check that the response is successful
    assert response.status_code == 200
    assert response.json()["filename"] == "test_file.txt"
    assert "filepath" in response.json()

    # Clean up
    uploaded_file_path = Path(response.json()["filepath"])
    if uploaded_file_path.exists():
        uploaded_file_path.unlink()  # Remove the uploaded file

    test_file_path.unlink()  # Remove the test file

# def test_get_users(client):
#     response = client.get('/api/users/')
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)  # Check if response is a list
#     assert len(response.json()) > 0  # Adjust based on expected output

# def test_create_user(client):
#     response = client.post('/api/users/', json={"name": "Test User"})
#     assert response.status_code == 201
#     assert response.json()["name"] == "Test User"
