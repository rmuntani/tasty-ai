from fastmcp import FastMCP
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from google import genai
from google.genai import types
from io import BytesIO

import base64

import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "ERROR"))

mcp = FastMCP(name="Images Server")

@mcp.tool()
def generate_image(text: str, additional_instructions: str) -> str:
    """Generates an image based on the given text description."""
    prompt = f"{additional_instructions}\nGenerate a detailed image for the following description:\n\n{text}"
    client = genai.Client()

    response = client.models.generate_images(
        model="models/imagen-3.0-generate-002",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images= 1,
        )
    )
    return [encode_image_to_base64(generated_image.image) for generated_image in response.generated_images][0]

def encode_image_to_base64(image) -> str:
    """Converts a PIL Image object to a Base64 string."""
    img_str = base64.b64encode(image.image_bytes)

    return img_str

if __name__ == "__main__":
    print("\n--- Starting FastMCP Server via __main__ ---")
    # This starts the server, typically using the stdio transport by default
    mcp.run()
