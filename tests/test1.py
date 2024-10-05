import requests

def make_get_request(a, b):
    try:
        response = requests.get('http://localhost:8000/test', params={'a': a, 'b': b})
        
        # Check if the request was successful
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        data = response.json()  # Parse JSON response
        print('Response data:', data)
    except requests.exceptions.RequestException as error:
        print('Error making GET request:', error)

# Example usage
make_get_request(5, 10)
