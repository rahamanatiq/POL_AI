import requests
import time

URL = "http://127.0.0.1:8000/api/ai/chat/"
QUERYs = [{"query": f"Test query {i}"} for i in range(10)]

print(f"Starting rate limiting verification on {URL}...")
print("The limit is set to 5 requests per minute for 'ai_chat' scope.")

for i, query in enumerate(QUERYs, 1):
    try:
        response = requests.post(URL, json=query)
        print(f"Request {i}: Status {response.status_code}")
        if response.status_code == 429:
            print("SUCCESS: Rate limit reached (429 Too Many Requests).")
            # print(f"Retry-After: {response.headers.get('Retry-After')}")
            break
        elif response.status_code != 200:
            print(f"FAILURE: Unexpected status code {response.status_code}")
            print(f"Response snippet: {response.text[:200]}")
            break
    except Exception as e:
        print(f"Error: {e}")
        break

print("Verification complete.")
