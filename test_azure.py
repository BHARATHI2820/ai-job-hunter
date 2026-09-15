import os

from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
api_key = os.getenv("AZURE_INFERENCE_API_KEY")
model = os.getenv("AZURE_INFERENCE_MODEL")
api_version = os.getenv("AZURE_API_VERSION")

print("Endpoint:", endpoint)
print("Model:", model)
print("API key loaded:", bool(api_key))
print("API version:", api_version)

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(api_key),
    api_version=api_version,
)

response = client.complete(
    messages=[
        {
            "role": "user",
            "content": "Say hello in one short sentence.",
        }
    ],
    model=model,
)

print("\nAzure response:")
print(response.choices[0].message.content)