from langgraph.graph import StateGraph
from langgraph.types import Command
from langgraph.types import Literal
from langgraph.graph import START
from langgraph.graph import END
from client import AgentClient
from state import State
import json
import sys
import os
import logging

from IPython.display import Image, display
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llm import LLM

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

class Graph:
    def __init__(self, agent_client: AgentClient = None):
       self.client = agent_client if agent_client else AgentClient()
       self.graph = self.setup_graph()
       self.state = {}

    def message(self, message: str) -> str:
        self.state = self.graph.invoke(self.state | { "message": message })
        return self.state['response']

    def setup_graph(self):
        builder = StateGraph(State)
        builder.add_conditional_edges(START, self.decide_action)
        
        # Recipe Selection
        
        # First Run
        builder.add_node(self.identify_language)
        builder.add_conditional_edges("identify_language", self.prevent_unknown_language)
        builder.add_node(self.translate_to_english)
        builder.add_edge("translate_to_english", "extract_preferences")
        builder.add_node(self.extract_preferences)
        builder.add_conditional_edges("extract_preferences", self.skip_if_no_recipe_needed)
        builder.add_node(self.recommend_recipes)

        builder.add_node(self.translate_recipe_options)
        builder.add_edge("recommend_recipes", "translate_recipe_options")
        
        # Command
        builder.add_node(self.update_or_select_recipe)
        
        # Recipe selected
        builder.add_node(self.select_recipe)
        builder.add_edge("select_recipe", "generate_image")
        builder.add_node(self.generate_image)
        builder.add_edge("generate_image", "responds_with_recipe")
        builder.add_node(self.responds_with_recipe)
        builder.add_edge("responds_with_recipe", END)
        
        # Update preferences
        builder.add_node(self.update_preferences)
        builder.add_edge("update_preferences", "recommend_recipes")
        
        # Informs the user of the agent's purpose and ignores messages it can't help with
        builder.add_node(self.unable_to_help)
        
        return builder.compile()
        
    def identify_language(self, state: State):
        message = state["message"]
        return state | { "language": self.client.run_identify_language(message) }

    def translate_to_english(self, state: State):
        message = state["message"]
        from_language = state["language"]
        to_language = "English"
    
        return state | { "enMessage": self.client.run_translate(message, from_language, to_language) }
    
    def extract_preferences(self, state: State):
        request = state["enMessage"]
    
        return state | { "preferences": self.client.run_define_preferences(request) }
    
    def recommend_recipes(self, state: State):
        preferences = state["preferences"]
        results = self.client.run_find_matches(preferences)
    
        return state | { "enRecipeOptions": results }
    
    def translate_recipe_options(self, state: State):
        recipe_options = state["enRecipeOptions"]
        to_language = state["language"]

        formatted_options = "".join([f"- {option['recipeTitle']}: {option['shortDescription']} Takes {option['timeToPrepare']} and has {option['calories']}\n" for option in recipe_options])
    
        text = f"""
Here are some recipe options:
{formatted_options}
Choose one of them, or let me know if you want to update your preferences.
        """
        translation = self.client.run_translate(text, "English", to_language)
    
        return state | { "translatedRecipeOptions": translation, "response": translation }
    
    def update_or_select_recipe(self, state: State) -> Command[Literal["select_recipe", "update_preferences", "unable_to_help"]]:
        prompt=f"""
        Given the following prompt in {state['language']}: {state['message']} and the recipe options {state['enRecipeOptions']} in English, 
        return a JSON with the user's choice. 
        If the user has mentioned one of the recipe options and wants to select it, return:
        {{ "action": "select_recipe", "recipeSelected": "Name of the recipe that matches the recipe options" }}.
        If the user wants a different recipe, or if it isn't clear that they chose a recipe, return:
        {{ "action": "update_preferences" }}.
        If the options above don't apply, return:
        {{ "action": "unable_to_help" }}
        Between "update_preferences" and "select_recipe", prioritize "select_recipe" if the user message indicates a choice.
        Only return one of the three options and no additional text.
        A few examples of expected behavior for some prompts:

        ```
        - Chicken Curry
        - Chicken with spicy sauce
        - Texmex Chicken
        ```
        'I want something with less spice' -> {{ "action": "update_preferences" }}


        ```
        - Chicken Curry
        - Chicken with spicy sauce
        - Texmex Chicken
        ```
        'Can you suggest other recipes with chicken?' -> {{ "action": "update_preferences" }}

        ```
        - Chicken Curry
        - Chicken with spicy sauce
        - Texmex Chicken
        ```
        'I would like to try the Spaghetti Bolognese' -> {{ "action": "update_preferences" }}

        ```
        - Chicken Curry
        - Chicken with spicy sauce
        - Texmex Chicken
        ```
        'I would like to try the Texmex Chicken' -> {{ "action": "select_recipe", "recipeSelected": "Texmex Chicken" }}

        ```
        - Chicken Curry
        - Chicken with spicy sauce
        - Texmex Chicken
        ```
        'The texan option sounds good' -> {{ "action": "select_recipe", "recipeSelected": "Texmex Chicken" }}

        ```
        - Chicken Curry
        - Chicken with spicy sauce
        - Texmex Chicken
        ```
        'Could you tell me a story about a chicken?' -> {{ "action": "unable_to_help" }}
        """
    
        llm = LLM(temperature=0.0)
        result = llm.model().invoke(prompt)
        option = json.loads(result.text.replace("```json", "").replace("```", ""))
    
        logger.info(f"Decided action: {option}")
    
        return  Command(
                update=state | { "recipeSelected": option["recipeSelected"] } if option["action"] == "select_recipe" else state,
                goto=option["action"]
                )
    
    def select_recipe(self, state: State) -> State:
        logger.info(f"User selected recipe: {state.get('recipeSelected', 'N/A')}")
        recipe_text = state['recipeSelected']
        recipe = [recipe for recipe in state['enRecipeOptions'] if recipe['recipeTitle'] == recipe_text][0]
        ingredients = "".join([f"- {ingredient}\n" for ingredient in recipe['ingredients']])
        instructions = "".join([f"{i+1}. {step}\n" for i, step in enumerate(recipe['instructions'])])

        recipe_text = f"""
Recipe Title: {recipe['recipeTitle']}

Short Description: {recipe['shortDescription']}

Calories: {recipe['calories']}

Time to Prepare: {recipe['timeToPrepare']}

Ingredients:
{ingredients}

Instructions:
{instructions}
        """

        logger.info(f"Recipe details: {recipe_text}")
    
        return { 'selectedRecipeDescription': recipe_text } | state
    
    def generate_image(self, state: State) -> State:
        recipe = state['selectedRecipeDescription']
    
        self.client.run_create_image(recipe, state['language'])
    
        return { 'imageGenerated': True } | state
    
    def responds_with_recipe(self, state: State) -> State:
        logger.info(f"Providing recipe details to user: {state.get('selectedRecipeDescription', 'N/A')}")
        selected_recipe = state['selectedRecipeDescription']
        result = f"""
Here are the details for your recipe:
{selected_recipe}
The recipe's image was saved to results.png
        """

        response = self.client.run_translate(result, 
                                             'English', 
                                             state['language'], 
                                             formatting="and turn it into a markdown and transform arrays into bullet points")

        return state | { 'response': response }
    
    def unable_to_help(self, state: State) -> State:
        logger.info("Unable to help with the current request.")
        from_language = state['language'] if state['language'] != "N/A" else "English"
    
        message = self.client.run_translate(f"We're currently unable to help with your request, but feel free to ask for recipes!", 
                                            "English", 
                                            from_language)
    
        return state | { 'response': message }
    
    def update_preferences(self, state: State) -> State:
        logger.info("Updating user preferences based on new request.")
        current_preferences = state['preferences']
        updated_request = state['message']
        suggestions = state['enRecipeOptions']
    
        en_message = self.client.run_translate(updated_request, state['language'], 'English')
        logger.info(f"Translated updated request to English: {en_message}")
        preferences = self.client.run_update_preferences(current_preferences, en_message, suggestions)
    
        return state | { 'preferences': preferences, "enMessage": en_message }
    
    def decide_action(self, state: State) -> str:
        if "language" not in state or state["language"] == "N/A":
            logger.info("Deciding to identify language")
            return "identify_language"
        elif "enRecipeOptions" in state:
            logger.info("Deciding to update or select recipe")
            return "update_or_select_recipe"
        else:
            logger.info("Extracting preferences and recommending recipes")
            return "translate_to_english"

    def prevent_unknown_language(self, state: State) -> str:
        if state["language"] == "N/A":
            logger.info("Language identified as N/A, unable to proceed.")
            return "unable_to_help"
        else:
            logger.info("Language identified successfully, proceeding to translation.")
            return "translate_to_english"

    def skip_if_no_recipe_needed(self, state: State) -> str:
        if "doesNotNeedRecipe" in state.get("preferences", {}) and state["preferences"]["doesNotNeedRecipe"]:
            logger.info("User does not need recipes, skipping to unable to help.")
            return "unable_to_help"
        else:
            logger.info("User needs recipes, proceeding to recommend recipes.")
            return "recommend_recipes"

