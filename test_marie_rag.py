import requests
import json

url = "http://127.0.0.1:8000/api/ai/marketplace-chat/"
headers = {"Content-Type": "application/json"}
data = {"query": "what aviation fuels do you have available?"}

response = requests.post(url, headers=headers, json=data)
print(json.dumps(response.json(), indent=2))
