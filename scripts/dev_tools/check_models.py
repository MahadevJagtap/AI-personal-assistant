
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("No GOOGLE_API_KEY found.")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
with open("models_available.txt", "w", encoding="utf-8") as f:
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(f"Name: {m.name}\n")
                print(f"Name: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
