import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

print("Model:", model)
print("API key loaded:", bool(api_key))

client = genai.Client(api_key=api_key)

print("[TEST] Calling Gemini Interactions API...", flush=True)

interaction = client.interactions.create(
    model=model,
    input="Find GenAI Engineer jobs in Chennai.",
)

print("[TEST] Interaction completed.", flush=True)
print("Interaction ID:", interaction.id)
print("Output:", interaction.output_text)