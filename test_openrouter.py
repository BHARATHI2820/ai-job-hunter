import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")

print("API key loaded:", bool(api_key))
print("Model:", model)

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Say hello in one short sentence.",
            }
        ],
    },
    timeout=60,
)

print("\nStatus:", response.status_code)

if response.ok:
    data = response.json()

    print("\nFull response:")
    import json
    print(json.dumps(data, indent=2))

else:
    print("Error:")
    print(response.text)