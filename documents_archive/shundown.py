import requests

try:
    response = requests.get("http://localhost:5001")
    if response.status_code == 200:
        print("Flask app is running on port 5001")
    else:
        print("Flask app is not responding correctly")
except requests.exceptions.RequestException as e:
    print("Flask app is not running on port 5001:", e)