import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/ai"

def test_context():
    results = {"lilian": [], "marie": []}
    
    print("Testing Lilian Context...")
    # Lilian Message 1
    q1 = "My favorite product is Aviation Fuel"
    resp1 = requests.post(f"{BASE_URL}/chat/", json={"query": q1})
    m1 = resp1.json().get('message')
    results["lilian"].append({"user": q1, "ai": m1})
    
    time.sleep(1)
    
    # Lilian Message 2
    q2 = "What did I just say my favorite product was?"
    resp2 = requests.post(f"{BASE_URL}/chat/", json={"query": q2})
    m2 = resp2.json().get('message')
    results["lilian"].append({"user": q2, "ai": m2})

    print("Testing Marie Context...")
    # Marie Message 1
    q3 = "I am looking for Aviation Fuel."
    resp3 = requests.post(f"{BASE_URL}/marketplace-chat/", json={"query": q3})
    m3 = resp3.json().get('message')
    results["marie"].append({"user": q3, "ai": m3})
    
    time.sleep(1)
    
    # Marie Message 2
    q4 = "What fuel was I looking for?"
    resp4 = requests.post(f"{BASE_URL}/marketplace-chat/", json={"query": q4})
    m4 = resp4.json().get('message')
    results["marie"].append({"user": q4, "ai": m4})

    with open("context_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to context_test_results.json")

if __name__ == "__main__":
    test_context()
