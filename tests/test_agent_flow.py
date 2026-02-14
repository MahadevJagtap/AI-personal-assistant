
import pytest
from agent.scheduler import meeting_scheduler

# We use the real agent here (with mocked tools/side-effects via fixtures)
# This requires GOOGLE_API_KEY to be valid.

def test_schedule_meeting_flow(client):
    """
    Test that asking to schedule a meeting actually calls the tool and updates the DB.
    """
    # 1. Send Request
    prompt = "Schedule a meeting with Client A for tomorrow at 10am for 1 hour."
    response = client.post("/chat", json={"message": prompt})
    
    assert response.status_code == 200
    reply = response.json()["response"]
    
    # 2. Verify Agent Reply
    # Agent should confirm
    assert "scheduled" in reply.lower() or "added" in reply.lower()
    
    # 3. Verify Scheduler State
    # The meeting should be in the list
    assert len(meeting_scheduler.meetings) == 1
    assert meeting_scheduler.meetings[0]["title"] == "Meeting with Client A" 
    # Note: Exact title matching depends on LLM extraction, but "Client A" should be there.
    assert "Client A" in meeting_scheduler.meetings[0]["title"]

def test_list_meetings_flow(client):
    """
    Test listing meetings functionality.
    """
    # Pre-seed a meeting
    meeting_scheduler.add_meeting("Unit Test Meeting", "2025-10-27 10:00", 30)
    
    prompt = "List my meetings."
    response = client.post("/chat", json={"message": prompt})
    
    assert response.status_code == 200
    reply = response.json()["response"]
    
    # Verify Agent lists it
    assert "Unit Test Meeting" in reply
    assert "2025-10-27" in reply

def test_send_email_flow(client, mock_smtp):
    """
    Test email sending workflow.
    """
    # Ensure creds are set for the service verification logic
    from agent.email_service import email_service
    email_service.email_address = "me@test.com"
    email_service.email_password = "pass"

    prompt = "Send an email to boss@example.com with subject 'Update' and body 'All good'."
    response = client.post("/chat", json={"message": prompt})
    
    assert response.status_code == 200
    reply = response.json()["response"]
    
    # Verify Agent confirmation
    assert "sent" in reply.lower()
    
    # Verify Mock SMTP Interaction
    # The service creates a new SMTP instance context manager each time.
    # mock_smtp is the class. instance is mock_smtp.return_value. context is __enter__ return value.
    instance = mock_smtp.return_value.__enter__.return_value
    instance.send_message.assert_called()
    
    # Inspect arguments if needed, but called is good enough for E2E flow.
