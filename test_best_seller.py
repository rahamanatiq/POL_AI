import requests

base_url = "http://127.0.0.1:8000/api/ai"
headers = {"Content-Type": "application/json"}

print("\n--- Testing Marie (FAISS RAG) for Best Price ---")
data = {"query": "i want to buy Transmission Fluid. give me best seller"}
response_marie = requests.post(f"{base_url}/marketplace-rag-chat/", headers=headers, json=data)
print(response_marie.json().get('message'))
