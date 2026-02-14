
import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.chat_agent import run_agent

def main():
    print("\nStarting AI Agent CLI...")
    print("Type 'exit' or 'quit' to stop.")
    print("-" * 30)

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting...")
                break
            
            if not user_input.strip():
                continue

            print("Agent: ", end="", flush=True)
            response = run_agent(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
