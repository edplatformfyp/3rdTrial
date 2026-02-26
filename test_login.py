import requests

url = "http://localhost:8000/auth/token"
data = {
    "username": "Rahul",
    "password": "password123"
}

try:
    print(f"Sending POST request to {url} with data: {data}")
    response = requests.post(url, data=data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
