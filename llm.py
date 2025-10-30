from langchain.chat_models import init_chat_model
import os

class LLM:
    def __init__(self, temperature: float = 0.0):
        self.llm = init_chat_model("google_genai:gemini-2.5-flash-lite", temperature=temperature)

    def model(self):
        return self.llm
