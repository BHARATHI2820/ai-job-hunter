import json
import os
import uuid

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential


class AzureLLM:
    def __init__(self, endpoint: str, api_key: str, model: str):
        self.model = model

        self.client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )

    def complete(self, messages: list[dict], tools: list[dict]):
        response = self.client.complete(
            messages=messages,
            tools=tools,
            model=self.model,
        )

        return response
    
def convert_tools_to_azure(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in tools
    ]