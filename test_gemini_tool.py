import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

print("Model:", model)
print("API key loaded:", bool(api_key))

client = genai.Client(api_key=api_key)

function = types.FunctionDeclaration(
    name="search_jobs",
    description="Search for jobs matching a role and location.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "role": {
                "type": "string",
                "description": "Job title or role, e.g. GenAI Engineer.",
            },
            "location": {
                "type": "string",
                "description": "City or Remote, e.g. Chennai.",
            },
        },
        "required": ["role", "location"],
    },
)

tool = types.Tool(
    function_declarations=[function]
)

print("[TEST] Calling Gemini with manual function declaration...", flush=True)

response = client.models.generate_content(
    model=model,
    contents="Find GenAI Engineer jobs in Chennai.",
    config=types.GenerateContentConfig(
        tools=[tool],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
    ),
)

print("[TEST] Gemini response received.", flush=True)

if response.function_calls:
    print("[TEST] SUCCESS - Tool call detected!", flush=True)

    for call in response.function_calls:
        print("Tool name:", call.name)
        print(
            "Tool arguments:",
            json.dumps(call.args, indent=2),
        )
else:
    print("[TEST] No tool call detected.", flush=True)
    print("Response:", response.text)