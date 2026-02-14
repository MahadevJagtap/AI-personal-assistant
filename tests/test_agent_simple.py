
import logging
from agent.chat_agent import run_agent

# Enable logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

def test_simple_agent():
    print("--- Testing Simple Agent Query ---")
    query = "List my meetings."
    print(f"\nUser Query: {query}")
    try:
        response = run_agent(query)
        print(f"\nAgent Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_agent()
