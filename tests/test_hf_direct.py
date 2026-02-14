
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
headers = {"Authorization": f"Bearer {api_token}"}

payload = {"inputs": "Hello, are you there?"}

try:
    print(f"Testing direct request to {API_URL}...")
    response = requests.post(API_URL, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
