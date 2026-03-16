import requests
import json

url = "http://127.0.0.1:8000/api/ai/rag-chat/"
headers = {"Content-Type": "application/json"}
data = {"query": "how many products i have in my inventory"}

response = requests.post(url, headers=headers, json=data)
print(json.dumps(response.json(), indent=2))
