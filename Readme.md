# Running the app

## Building the Docker image

```bash
docker build . -t tasty-ai
```

## Running the MCP servers

Make sure the image is built, then run:

```bash
 docker compose up
```

For the LLM and image generation services to work, you must define a docker-compose.override.yml with the following
structure:

```
services:
  food:
    environment:
    - GOOGLE_API_KEY=KEY

  language:
    environment:
    - GOOGLE_API_KEY=KEY

  image:
    environment:
    - GOOGLE_API_KEY=KEY

  agent:
    environment:
    - GOOGLE_API_KEY=KEY
```

## Running the agent

```
docker compose exec agent python3 agent.py
```

## Loading the recipes

The setup below doesn't levarage GPUs. 
```
// Make sure the dataset is in full_dataset.csv
docker compose exec mcp-server python3 load_data.py
```

## Architecture

### Technologies

- Gemini: 
    - Gemini was chosen for convenience and its generous free tier and credits for new users
    - LLM: google_genai:gemini-2.5-flash-lite
    - Image Generation: imagen-3.0-generate-002

- Vector Database: ChromaDB 
    - It is an open-source vector database that is easy to use and set up. Some of the content in the
    course used it, so it was a natural choice.

- fastMCP:
    - It was used to simplify developing the servers that are consumed by the agent. The resulting servers
    are rather shallow, mostly wrapping calls to the LLM or image generation models, but it was a nice opportunity
    to learn how to use fastMCP.

- langgraph:
    - One of the recommended tools for building agents. It's simple to use and its graph representation makes it easier
    to document and shape the flow of informations

### Architecture

#### MCP Servers

The main idea was to separate the system into specialized components that are coordinated by the agent. The main abstractions
I thought were useful were:

- Language: MCP server that handles identifying the language and translating tasks. It's mostly a wrapper around the LLM if 
  prompt to identify the language used by the user and translate messages from and to English;

- Food: given a message, a service that identifies the user's preferences and recommends recipes according to them. The recipes
  are stored in a vector database and retrieved using embeddings according to the usr's preferences. The LLM is used to parse the 
  user's preferences, choose recipes that align with preferences, and parse recipe details. If I had the chance to improve it, I would
  make its API more concise, removing the need to have multiple calls from the agent. I don't think the MCP Server should expose to
  the client what are preferences. It could have been a separate agent;

- Image: MCP server that is a shallow wrapper around the image generation model. It receives a prompt and returns the image URL. 

#### Agent

The agent orchestrates the calls to these services, maintaining the context of the conversation and deciding what to do next. It relies
on the AgentClient to perform the requests. Here's its behavior:

[agent graph image](./agent_graph.png)

##### Methodology

I started by testing each one of the MCPs separately, making sure they worked as expected. As each method was ready, I added nodes to
the agent graph, testing the overall behavior as I went.

##### Improvements

- classifying what the user wants to do on a following message is imprecise in the way I did it. A next step could be to have a more robust
  classification system, which could use more robust prompting or even fine-tuning; 

- the dataset of recipes lacked informations that are very important, like calory count, time to prepare, or tools required for the recipe. A
  next step could be to augment the dataset with this information, either by webscraping, using the LLM to fill in the gaps, or applying some
  logic to the existing data. My solution was to use LLM prompting to estimate these values for the recipes that match the arbitrary search;

- updating preferences could be improved a lot. I don't think it captures the new priorities very well all of the time unless the request is
  direct;

- the error handling is very basic. The agent just retries once if a request fails; 

- I'm not very productive with Python, so development was slower than expected;

- automated tests for the graph while mocking the MCP servers would be a nice addition;

### Examples

#### Video with image

[./example-use.mov](./example-use.mov)

#### Sending random text

```
fidfidjfisjfidsjfidsjfidsj0r923ir923iu 999911212
----------------
We're currently unable to help with your request, but feel free to ask for recipes!jfisjfidsjfidsjfidsj0r923ir923iu 999911212
```

### Straightforward recipe request

```
Hey! I want an australian dish.
----------------

Here are some recipe options:
- Chicken & Seafood Paella - Australian Women's Weekly: A flavorful Australian-inspired paella featuring chicken and seafood. Takes 1 hour 15 minutes and has 600-700 kcal
- Bobotie - South African Cape Malay Casserole: A comforting and flavorful South African Cape Malay casserole popular in Australia. Takes 1 hour 30 minutes and has 450-550 kcal
- Malaysian Satays: Authentic Malaysian satays, a beloved dish with significant influence on Australian food culture. Takes 3 hours 30 minutes and has 400-500 kcal

Choose one of them, or let me know if you want to update your preferences.
        
----------------
Bobotie sounds good.
----------------

Here are the details for your recipe:

Recipe Title: Bobotie - South African Cape Malay Casserole

Short Description: A comforting and flavorful South African Cape Malay casserole popular in Australia.

Calories: 450-550 kcal

Time to Prepare: 1 hour 30 minutes

Ingredients:
- Ground beef or lamb
- Onion
- Garlic
- Curry powder
- Turmeric
- Cumin
- Coriander
- Apricot jam
- Raisins or sultanas
- Almonds (slivered)
- Bread (soaked in milk)
- Eggs
- Milk
- Bay leaves
- Salt and pepper
- Oil or butter


Instructions:
1. Sauté chopped onion and garlic in oil until softened.
2. Add ground meat and brown it.
3. Stir in curry powder, turmeric, cumin, coriander, salt, and pepper.
4. Add apricot jam, raisins, and slivered almonds.
5. Squeeze excess milk from soaked bread and add it to the meat mixture, mixing well.
6. Transfer the mixture to a baking dish.
7. Whisk together eggs and milk, then pour over the meat mixture.
8. Place bay leaves on top.
9. Bake in a preheated oven at 180°C (350°F) for about 40-50 minutes, or until the topping is set and golden brown.
        
The recipe's image was saved to results.png
```

#### Asking for something that's not a recipe and asking for a recipe

```
Give me money.
----------------
We're currently unable to help with your request, but feel free to ask for recipes!
----------------
Sorry. I want an australian recipe with lamb and onions.
----------------

Here are some recipe options:
- Australian Lamb Leg Tagine With Warm Couscous: A flavorful Australian-inspired lamb tagine with warm couscous, featuring tender lamb, aromatic spices, and sweet fruits. Takes 1 hour 30 minutes to 2 hours and has 500-600 kcal
- Mark's Aussie Bolognaise: A hearty and comforting Australian-inspired bolognaise made with ground lamb and a rich tomato sauce. Takes 40-50 minutes and has 400-500 kcal
- Curried Australian Lamb Chops With Caper Aioli: Tender, marinated Australian lamb chops with a zesty caper aioli, infused with curry flavors. Takes 25-30 minutes cooking time, plus at least 24 hours for marinating and has 600-700 kcal

Choose one of them, or let me know if you want to update your preferences.
        
----------------
Australian Lamb Leg sounds delicious.
----------------

Here are the details for your recipe:

Recipe Title: Australian Lamb Leg Tagine With Warm Couscous

Short Description: A flavorful Australian-inspired lamb tagine with warm couscous, featuring tender lamb, aromatic spices, and sweet fruits.

Calories: 500-600 kcal

Time to Prepare: 1 hour 30 minutes to 2 hours

Ingredients:
- 1 1/2-2 lb boneless australian lamb leg
- 1 tsp ground cumin
- 1 tsp ground cinnamon
- 1 tsp ground ginger
- 1 tsp ground coriander
- 2 tbsp olive oil
- 1 onion, chopped
- 1 leek, white part only, sliced
- 2 medium carrots, chopped
- 1 1/2 cups chicken stock or broth
- 1/2 cup raisins
- 2 large tomatoes, coarsely chopped
- 1 pear, diced
- cooked couscous, warm
- 1/4 cup pine nuts
- salt and pepper to taste


Instructions:
1. Trim and dice lamb into bite-sized pieces. Combine the next 4 ingredients (cumin, cinnamon, ginger, coriander) and divide in half. In a heavy-based skillet, add the lamb and half the spices. Cook, stirring until browned. Transfer lamb to a plate and drain fat from pan.
2. Heat the remaining oil and spices in the same pan over medium heat for about 30 seconds. Add onion, leek, and carrots. Cook until onion is softened. Return meat to the pan with the stock, raisins, and tomatoes and stir well. Cover, reduce heat to low, and simmer for 1 hour.
3. Add pear and simmer, uncovered, for 20-30 minutes or until lamb is tender and sauce is thick. Spoon tagine over the warm couscous, sprinkle with pine nuts. Serve.

        
The recipe's image was saved to results.png
----------------
```

#### Back and forth interaction in portuguese

```
Quero um prato com queijo e maçã. 
----------------
Aqui estão algumas opções de receitas:
- Maçãs com Queijo: Um prato de maçã assada com uma cobertura crocante e de queijo. Leva de 35 a 45 minutos e tem de 450 a 550 kcal
- Sobremesa de Maçã com Queijo: Uma sobremesa simples de maçã assada com uma cobertura de queijo e canela. Leva 45 minutos e tem de 300 a 400 kcal
- Famosa Maçã com Queijo: Uma caçarola em camadas de maçã assada e queijo com cobertura de bolacha. Leva de 35 a 45 minutos e tem de 500 a 600 kcal

Escolha uma delas, ou me diga se quer atualizar suas preferências.
----------------
Pode tirar o queijo e manter a maçã? Quero sim uma sobremesa.
----------------
Aqui estão algumas opções de receitas:
- Sobremesa de Maçã (Rápida e Fácil): Uma sobremesa de maçã rápida e fácil com uma cobertura crocante. Leva 30 minutos e tem 350-450 kcal
- Sobremesa de Maçã: Uma sobremesa de maçã clássica com uma textura úmida semelhante a um bolo. Leva 40-50 minutos e tem 300-400 kcal
- Sobremesa de Maçã Simples (Receita com Baixas Calorias): Uma sobremesa de maçã simples e com poucas calorias feita no micro-ondas. Leva 15-20 minutos e tem 60 calorias por meia xícara

Escolha uma delas, ou me diga se você quer atualizar suas preferências.
----------------
Massa, adorei as opções. Eu quero a sobremesa de maçã rápida e fácil.
----------------
# Sobremesa de Maçã (Rápida e Fácil)

Uma sobremesa de maçã rápida e fácil com uma cobertura crocante.

**Calorias:** 350-450 kcal

**Tempo de Preparo:** 30 minutos

**Ingredientes:**
* 1 lata de maçãs ou maçãs frescas (3 ou 4)
* 1 xícara de farinha
* 1 xícara de açúcar mascavo claro
* 1 xícara de aveia
* 1/2 xícara de gordura vegetal (Crisco)
* 1 colher de chá de canela

**Instruções:**
1. Escorra as maçãs.
2. Misture os ingredientes com os dedos.
3. Espalhe 1/2 da mistura em uma forma quadrada, adicione as maçãs misturadas com canela, e depois o restante da mistura.
4. Asse a 175°C por 20 minutos.

A imagem da receita foi salva em results.png
```
