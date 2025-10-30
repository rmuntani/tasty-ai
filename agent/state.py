from typing_extensions import TypedDict

class State(TypedDict):
    language: str
    message: str
    enMessage: str
    preferences: dict[str, str]
    enRecipeOptions: dict
    recipeSelected: str
    translatedRecipeOptions: str
    imageGenerated: bool
    selectedRecipeDescription: str
    response: str
    suggestedDescription: str
