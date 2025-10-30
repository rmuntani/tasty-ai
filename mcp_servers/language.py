from fastmcp import FastMCP
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llm import LLM

import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "ERROR"))

mcp = FastMCP(name="Language Server")

@mcp.tool()
def find_language(text: str) -> str:
    """Find the language of the given text."""
    prompt = f"""
    Identify the language of the following text. Only return its name. If you can't determine the language, assume it's N/A.
    {text}
    """
    response = LLM(temperature=0.0).model().invoke(prompt)

    return response.text()

@mcp.tool()
def translate(text: str, fromLanguage: str, toLanguage: str, formatting: str = "keep formatting") -> str:
    """Translate text from one language to another."""
    if fromLanguage.lower() == toLanguage.lower():
        return text

    prompt = f"""
    Translate the following text from {fromLanguage} to {toLanguage}. Provide a single answer with nothing but the message 
    translated and {formatting}.
    {text}
    """
    response = LLM(temperature=0.0).model().invoke(prompt)

    return response.text()

if __name__ == "__main__":
    print("\n--- Starting FastMCP Server via __main__ ---")
    # This starts the server, typically using the stdio transport by default
    mcp.run()
