import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent')))
from graph import Graph
from client import AgentClient

logging.basicConfig(level=logging.INFO)

agent_client = AgentClient(
        language_server_path='http://language:8002/mcp', 
        food_server_path='http://food:8001/mcp', 
        image_server_path='http://image:8003/mcp'
        )
graph = Graph(agent_client=agent_client)

while True:
    try:
        # Prompt the user for input
        message = input("")

        print("----------------")

        # Check if the user wants to quit (case-insensitive)
        if message.lower() in ('quit', 'exit'):
            print("\nEcho loop terminated. Goodbye!")
            break

        new_message = graph.message(message)

        print(new_message)

        print("----------------")

    except EOFError:
        # Handles the case where the input stream is closed (e.g., Ctrl+D)
        print("\nInput stream closed. Exiting.")
        break
    except KeyboardInterrupt:
        # Handles the case where the user presses Ctrl+C
        print("\nProgram interrupted by user. Exiting.")
        break
