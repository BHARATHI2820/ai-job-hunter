import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")

print("API key loaded:", bool(api_key))
print("Model:", model)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "Search for jobs matching a role and location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "Job title or role, e.g. 'GenAI Engineer'.",
                    },
                    "location": {
                        "type": "string",
                        "description": "City or 'Remote', e.g. 'Chennai'.",
                    },
                },
                "required": ["role", "location"],
            },
        },
    }
]

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
                "content": "Find GenAI Engineer jobs in Chennai.",
            }
        ],
        "tools": tools,
        "tool_choice": "auto",
    },
    timeout=60,
)

print("\nStatus:", response.status_code)

if response.ok:
    data = response.json()

    message = data["choices"][0]["message"]

    print("\nAssistant content:")
    print(message.get("content"))

    print("\nTool calls:")
    tool_calls = message.get("tool_calls")

    if tool_calls:
        for tool_call in tool_calls:
            print("Tool name:", tool_call["function"]["name"])
            print("Arguments:")
            print(json.dumps(
                json.loads(tool_call["function"]["arguments"]),
                indent=2
            ))
    else:
        print("No tool call returned.")

    print("\nUsage:")
    print(json.dumps(data.get("usage", {}), indent=2))

else:
    print("\nError:")
    print(response.text)