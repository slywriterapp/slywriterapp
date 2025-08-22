import requests
import json

# Set user to pro plan on Render server
user_id = "103752276849392048030"
url = "https://slywriterapp.onrender.com/set_plan"

data = {
    "user_id": user_id,
    "plan": "pro"
}

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! User {user_id} set to {result.get('plan')} plan")
    else:
        print(f"❌ Failed with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")