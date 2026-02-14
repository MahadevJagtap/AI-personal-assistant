
import os
import sys
from agent.memory import agent_memory, ChatHistory, Session

def test_memory():
    print("--- Testing Memory System ---")

    # 1. Clear existing memory
    print("Clearing memory...")
    agent_memory.clear_memory()
    
    # 2. Add interactions
    print("Adding interaction 1...")
    agent_memory.add_to_memory("Hi, I am Shubh.", "Hello Shubh! How can I help?")
    
    print("Adding interaction 2...")
    agent_memory.add_to_memory("What is my name?", "Your name is Shubh.")

    # 3. Verify Buffer (Short-term)
    print("\n--- Verifying Buffer ---")
    history = agent_memory.get_history()
    print("History in Buffer:\n", history)
    assert "Shubh" in history
    assert "Your name is Shubh" in history

    # 4. Verify DB (Persistence)
    print("\n--- Verifying Database ---")
    session = Session()
    msgs = session.query(ChatHistory).all()
    session.close()
    
    print(f"Found {len(msgs)} messages in DB.")
    for m in msgs:
        print(f"[{m.role}] {m.content}")
    
    assert len(msgs) == 4 # 2 turns * 2 messages each
    
    # 5. Verify Reloading
    print("\n--- Verifying Reload on Init ---")
    # Simulate restarting agent by creating new instance
    new_memory = agent_memory.__class__() 
    reloaded_history = new_memory.get_history()
    print("Reloaded History:\n", reloaded_history)
    
    assert history == reloaded_history
    print("\n✅ Memory Test Passed!")

if __name__ == "__main__":
    try:
        test_memory()
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
