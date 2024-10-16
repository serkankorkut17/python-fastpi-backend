# import pytest

# def test_get_users(client):
#     response = client.get('/api/users/')
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)  # Check if response is a list
#     assert len(response.json()) > 0  # Adjust based on expected output

# def test_create_user(client):
#     response = client.post('/api/users/', json={"name": "Test User"})
#     assert response.status_code == 201
#     assert response.json()["name"] == "Test User"
