#!/usr/bin/env python3
import requests
import json

def test_memory():
    url = "https://copiloto-semantico-func-us2.azurewebsites.net/api/ejecutar"
    payload = {
        "session_id": "verify_test",
        "intencion": "dashboard"
    }
    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": "verify_test"
    }
    
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    data = resp.json()
    
    print("Status:", resp.status_code)
    print("Has metadata:", "metadata" in data)
    if "metadata" in data:
        metadata = data["metadata"]
        print("Memory available:", metadata.get("memoria_disponible"))
        print("Wrapper applied:", metadata.get("wrapper_aplicado"))
        print("Session info:", metadata.get("session_info"))
        return True
    return False

if __name__ == "__main__":
    success = test_memory()
    print("Memory system working:", success)