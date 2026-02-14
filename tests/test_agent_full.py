
import unittest
from agent.chat_agent import run_agent

# Note: This test interacts with real (or mocked) services 
# dependent on previous setup. 
# It requires Gemini Key to be set.

def test_full_agent():
    print("--- Testing Full Agent Orchestration ---")
    
    # Complex Query requiring multiple tools potentially, 
    # or at least understanding two distinct requests.
    # "Schedule a meeting... AND send an email..."
    # Note: AgentExecutor with Gemini Flash is usually capable of sequential tool calling.
    
    query = "Schedule a meeting with Client X for tomorrow at 10am for 1 hour. Also list my meetings to confirm."
    
    print(f"\nUser Query: {query}")
    response = run_agent(query)
    print(f"\nAgent Response: {response}")
    
    if "list" in response.lower() or "schedule" in response.lower() or "meeting" in response.lower():
         print("✅ Agent responded relevantly.")
    else:
         print("❌ Agent response seems unrelated. Check logs.")

if __name__ == "__main__":
    test_full_agent()
