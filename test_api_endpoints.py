import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/ai"

def test_endpoint(name, method, url, payload=None):
    print(f"\n========================================================")
    print(f"Testing: {name}")
    print(f"URL: {method} {url}")
    if payload:
        print(f"Payload: {json.dumps(payload)}")
    print(f"-------------------------------------------------------")
    
    try:
        start_time = time.time()
        if method == "POST":
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        else:
            response = requests.get(url)
        end_time = time.time()
        
        print(f"Status Code: {response.status_code} (took {end_time - start_time:.2f}s)")
        
        try:
            resp_json = response.json()
            if "message" in resp_json:
                print(f"AI Message:\n---> {resp_json['message']}")
            print(f"\nRaw JSON Response:")
            # Print truncated JSON to keep output readable
            json_str = json.dumps(resp_json, indent=2)
            if len(json_str) > 1000:
                print(json_str[:1000] + "\n... [truncated] ...")
            else:
                print(json_str)
        except json.JSONDecodeError:
            print(f"Response was not valid JSON. Raw text:\n{response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("Make sure 'python manage.py runserver' is running on port 8000.")

def run_tests():
    # 1. Test Lilian's Initial Greeting
    test_endpoint(
        name="Lilian Greeting (Conversational)",
        method="POST",
        url=f"{BASE_URL}/chat/",
        payload={"query": "hi, what's your name?"}
    )
    
    # 2. Test Lilian's Inventory Search (Mock Data Request)
    test_endpoint(
        name="Lilian Inventory Search",
        method="POST",
        url=f"{BASE_URL}/chat/",
        payload={"query": "I need products related to fuel maintenance or petrol."}
    )
    
    # 3. Test Marie's Initial Welcome Request
    test_endpoint(
        name="Marie Welcome Message",
        method="GET",
        url=f"{BASE_URL}/marketplace-chat/"
    )

    # 4. Test Marie's Marketplace Search (Mock Data Request)
    test_endpoint(
        name="Marie Marketplace Search",
        method="POST",
        url=f"{BASE_URL}/marketplace-chat/",
        payload={"query": "Who is selling the cheapest aviation fuel?"}
    )

if __name__ == "__main__":
    print("Starting API Endpoint Tests using mock query data...")
    print("Ensure the Django server is running locally.")
    run_tests()
