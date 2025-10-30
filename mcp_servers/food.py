from fastmcp import FastMCP
import sys
import os
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llm import LLM
from db import VectorDatabase

import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

mcp = FastMCP(name="Food Server")

db = VectorDatabase()

assistant = f"""
    You're an assistant chef that helps people find the best recipe given their instructions. You figure out if they need a recipe, suggest recipes
    to them, and once they choose one of the selected recipes, you provide them with the full recipe details.
    """

preferences_schema = {
        "references": {
            "type": "string",
            "description": "A recipe name, ingredients, or keywords that are important according to the user request. This is the most important field and should always be populated",
            "required": True
            },
        "diet": {
            "type": "string",
            "description": "The user's dietary preferences, e.g., vegetarian, vegan, keto, savory, dessert, etc."
            },
        "cuisine": {
            "type": "string",
            "description": "The type of cuisine the user prefers, e.g., Italian, Chinese, Mexican, etc."
            },
        "mealType": {
            "type": "string",
            "description": "The type of meal the user wants, e.g., breakfast, lunch, dinner, snack, dessert."
            },
        "timeSpentCooking": {
            "type": "string",
            "description": "The amount of time the user is willing to spend cooking in vague terms, e.g., quick, moderate, long.",
            "enum": ["short", "moderate", "long", "N/A"]
            },
        "includeIngredients": {
            "type": "array",
            "items": {
                "type": "string"
                },
            "description": "List of ingredients the user wants to include"
            }, 
        "excludeIngredients": {
            "type": "array",
            "items": {
                "type": "string"
                },
            "description": "List of ingredients the user wants to exclude"
            },
        "complexity": {
            "type": "string",
            "description": "The desired complexity of the recipe, e.g., easy, medium, hard.",
            "enum": ["easy", "medium", "hard", "N/A"]
            },
        "doesNotNeedRecipe": {
                "type": "boolean",
                "description": "Indicates whether the user has requested a recipe. This field has to be present.",
                "default": False,
                "required": True
                },
        "caloriesPreference": {
            "type": "string",
            "description": "The user's calorie preference for the recipe, e.g., low-calorie, high-protein, balanced.",
            "enum": ["low", "medium", "high", "N/A"]
            }
}

@mcp.tool()
def define_preferences(text: str) -> str:
    """Defines food preferences for a given text."""
    prompt = f"""
        {assistant}
        Based on the following Schema and Instructions, return the user's preferences JSON. If they don't want a recipe, set doesNotNeedRecipe to true.
        Instructions: 
            {text}
        Schema: 
            {preferences_schema}
    """

    response = LLM(temperature=0.0).model().invoke(prompt)

    return response.text()

@mcp.tool()
def update_preferences(currentPreferences: dict, updatedRequest: str, suggestions: list) -> str:
    """Updates food preferences based on user feedback."""
    prompt = f"""
        {assistant}
        The user didn't like the previous recipe suggestions:
        {suggestions}
        Due to that, they provided updated instructions:
        {updatedRequest}
        And their initial preferences were:
        {currentPreferences}
        Based on that, return the updated preferences JSON according to the Schema. Make sure to exclude what
        the user doesn't want and include what they do want.
        If they want a quicker recipe, a simpler one, or less calories, make sure to change the fields accordingly.
        Schema: {preferences_schema}
    """

    response = LLM(temperature=0.0).model().invoke(prompt)

    return response.text()
        

@mcp.tool()
def find_matches(preferences: dict) -> list:
    """Finds recipe matches based on food preferences."""
    recommendations = get_matches(preferences)
    logger.info(f"Raw recommendations: {recommendations}")
    formatted_recommendations = to_json(recommendations)
    logger.info(f"Formatted recommendations: {formatted_recommendations}")

    return formatted_recommendations

def get_matches(preferences: dict) -> str:
    strs = [
           preferences.get('diet', None),
           preferences.get('cuisine', None),
           preferences.get('mealType', None),
           f"using {''.join(preferences['includeIngredients'])}" if preferences.get('includeIngredients', None) else None,
           f"without {''.join(preferences['excludeIngredients'])}" if preferences.get('excludeIngredients', None) else None]

    text = " ".join(s.strip() for s in strs if s and s.strip())
    reference = preferences['references']

    results = db.search([reference, text], n_results=10)
    documents = results['documents']

    prompt = f"""
    {assistant}

    Based on the following preferences and search results, find the three best matching recipe. If the recipe doesn't respect the constraints 
    (e.g. it includes dairy when it should be dairy free), do not recommend it or suggest substitutions. Estimate the calories per serving and
    time to prepare the recipe to help with the decision. If two or more recipes are very similar, exclude the duplicates. Consider the ingredients
    and steps, and include them in the result.

    Preferences: 
        {preferences}

    Search Results: 
        {documents}

    Think step by step to ensure the best results.
    """

    return LLM(temperature=0.0).model().invoke(prompt).text

def to_json(recommendations: str) -> list:
    format_prompt = f"""
    Format the following recipe recommendations into a JSON array. Each recommendation should have the following fields:
    {{ 
        "calories": string,
        "timeToPrepare": string,
        "shortDescription": string,
        "recipeTitle": string,
        "ingredients": [string],
        "instructions": [string],
        "fullDescription": string
    }}
    The full description should include all other fields in the json in a well formatted manner.
    Example: 
    [
        {{
            "calories": "500 kcal",
            "timeToPrepare": "30 minutes",
            "shortDescription": "A quick and easy pasta dish with tomatoes and basil.",
            "recipeTitle": "Tomato Basil Pasta",
            "ingredients": ["200g pasta", "2 cups cherry tomatoes", "1/4 cup fresh basil", "2 cloves garlic", "2 tbsp olive oil", "Salt and pepper to taste"],
            "instructions": ["Cook pasta according to package instructions.", "In a pan, heat olive oil and sauté garlic.", "Add cherry tomatoes and cook until soft.", "Mix in cooked pasta and fresh basil.", "Season with salt and pepper."],
        }}
    ]
    Recipes:
    {recommendations}
    """ 

    response = LLM(temperature=0.0).model().invoke(format_prompt)
    return json.loads(response.text.replace("```json", "").replace("```", ""))


if __name__ == "__main__":
    print("\n--- Starting FastMCP Server via __main__ ---")
    # This starts the server, typically using the stdio transport by default
    mcp.run()
