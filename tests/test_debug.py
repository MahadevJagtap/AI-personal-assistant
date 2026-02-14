
import pytest
from agent.scheduler import meeting_scheduler

def test_debug_flow(client):
    print("\n--- Debug Flow ---")
    # 1. Simple Hello to check agent/LLM connectivity
    try:
        response = client.post("/chat", json={"message": "Hello"})
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Hello Check Failed: {e}")

    # 2. Schedule
    try:
        response = client.post("/chat", json={"message": "Schedule a meeting called 'Debug Meet' for tomorrow at 9am."})
        print(f"Schedule Status: {response.status_code}")
        print(f"Schedule Body: {response.text}")
    except Exception as e:
        print(f"Schedule Check Failed: {e}")

    print(f"Scheduler Internal Meetings: {meeting_scheduler.meetings}")
