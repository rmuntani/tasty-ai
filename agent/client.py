from fastmcp import Client
import asyncio
import json
import base64
import logging

logger = logging.getLogger(__name__)

class AgentClient:
    def __init__(self, language_server_path='mcp_servers/language.py', food_server_path='mcp_servers/food.py', image_server_path='mcp_servers/images.py'):
        self.language_server_path = language_server_path
        self.food_server_path = food_server_path
        self.image_server_path = image_server_path

    def run_identify_language(self, message: str) -> str:
        async def identify_language(message: str) -> str:
            language = None
            client = Client(self.language_server_path)
        
            try:
                async with client:
                    result = await client.call_tool("find_language", {"text": message})
                    language = result.data
            except Exception as e:
                logger.info(f"An error occurred: {e}")
                language = "N/A"
            finally:
                logger.info(f"Client interaction finished")
        
            return language

        return asyncio.run(identify_language(message))
    
    def run_translate(self, message: str, from_language: str, to_language: str, formatting: str = "keep formatting") -> str:
        async def translate(message: str, from_language: str, to_language: str, formatting: str) -> str:
            translated_message = None
            client = Client(self.language_server_path)
    
            try:
                async with client:
                    logger.info(f"Translating from {from_language} to {to_language}")
                    result = await client.call_tool("translate", {
                        "text": message,
                        "fromLanguage": from_language,
                        "toLanguage": to_language,
                        "formatting": formatting
                    })
                    translated_message = result.data
            except Exception as e:
                logger.info(f"An error occurred: {e}")
                translated_message = message
            finally:
                logger.info(f"Client interaction finished")
    
            logger.info(f"Translated message: {translated_message}")

            return translated_message
        return asyncio.run(translate(message, from_language, to_language, formatting))
    
    def run_define_preferences(self, request: str) -> dict[str, str]:
        async def define_preferences(request: str) -> dict[str, str]:
            preferences = None
            client = Client(self.food_server_path)

            try:
                async with client:
                    result = await client.call_tool("define_preferences", {"text": request})
                    logger.info(f"Raw preferences: {result.data}")
                    preferences = json.loads(result.data.replace("```json", "").replace("```", ""))
            except Exception as e:
                logger.info(f"An error occurred: {e}")
                preferences = {}
            finally:
                logger.info(f"Client interaction finished")

            return preferences
        return asyncio.run(define_preferences(request))

    def run_update_preferences(self, current_preferences: dict, updated_request: str, suggestions: str) -> dict[str, str]:
        async def update_preferences(current_preferences: dict, updated_request: str, suggestions: str) -> dict[str, str]:
            updated_preferences = None
            client = Client(self.food_server_path)

            try:
                async with client:
                    result = await client.call_tool("update_preferences", {
                        "currentPreferences": current_preferences,
                        "updatedRequest": updated_request,
                        "suggestions": suggestions
                        })
                    logger.info(f"Raw updated preferences: {result.data}")
                    updated_preferences = json.loads(result.data.replace("```json", "").replace("```", ""))
            except Exception as e:
                logger.info(f"An error occurred: {e}")
                updated_preferences = current_preferences
            finally:
                logger.info(f"Client interaction finished")

            return updated_preferences
        return asyncio.run(update_preferences(current_preferences, updated_request, suggestions))

    def run_find_matches(self, preferences: dict) -> str:
        async def find_matches(preferences: dict) -> str:
            recipe = None
            client = Client(self.food_server_path)

            try:
                async with client:
                    result = await client.call_tool("find_matches", {"preferences": preferences})
                    logger.info(f"Raw recipe recommendation: {result.data}")
                    recipe = result.data
            except Exception as e:
                logger.info(f"An error occurred: {e}")
                recipe = {}
            finally:
                logger.info(f"Client interaction finished")

            return recipe
        return asyncio.run(find_matches(preferences))

    def run_create_image(self, recipe: str, from_language: str) -> None:
        async def create_image(recipe_text: str, from_language: str) -> None:
            client = Client(self.image_server_path)

            try:
                async with client:
                    logger.info(f"Getting image")
                    result = await client.call_tool("generate_image", {
                        "text": recipe,
                        "additional_instructions": "You are a professional food photographer. Generate a high-quality, appetizing image of the finished dish described in the recipe. Focus on the dish and only the dish"
                        })
                    base64_string = result.data

                    image_data = base64.b64decode(base64_string)

                    with open("results.png", "wb") as image_file:
                        image_file.write(image_data)

                    logger.info("Image saved successfully as results.png")
            except Exception as e:
                logger.info(f"An error occurred: {e}")
            finally:
                logger.info(f"Client interaction finished")

        asyncio.run(create_image(recipe, from_language))
        return None
