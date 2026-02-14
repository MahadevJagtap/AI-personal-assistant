
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
headers = {"Authorization": f"Bearer {api_token}"}

models_to_test = [
    "HuggingFaceH4/zephyr-7b-beta",
    "google/gemma-2-9b-it",
    "google/flan-t5-large",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "gpt2",
    "google/flan-t5-base",
    "facebook/opt-125m"
]

payload = {"inputs": "Hello, are you there?"}

for model in models_to_test:
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    print(f"\nTesting {model}...")
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Response: {response.json()}")
            break # Found a working one
        else:
            print(f"Failed. Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
