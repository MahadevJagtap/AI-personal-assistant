
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_meetings_empty(client):
    response = client.get("/meetings")
    assert response.status_code == 200
    # Expecting empty list initially or from temp file
    data = response.json()
    assert "meetings" in data
    assert isinstance(data["meetings"], list)

def test_chat_simple(client):
    # Mock run_agent to avoid hitting LLM for simple API test
    # We want to test the endpoint logic, not the LLM here.
    with unittest.mock.patch("api.main.run_agent", return_value="Mocked response"):
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 200
        assert response.json() == {"response": "Mocked response"}

import unittest.mock

def test_email_endpoint(client):
    # SMTP is already mocked by autouse fixture in conftest
    # But we want to ensure the service returns success
    
    # We also need to patch the email_service.send_email method? 
    # Or rely on the mocked SMTP inside it?
    # The `email_service` imports `smtplib`. Conftest mocks `agent.email_service.smtplib.SMTP`.
    # So `send_email` should execute logic, hit mock SMTP, and return success string.
    
    # We need to ensure credentials exist in env or are mocked in service instance
    # The service loads env at generic import time.
    # Let's patch the instance credentials.
    from agent.email_service import email_service
    email_service.email_address = "test@example.com"
    email_service.email_password = "password"
    
    response = client.post("/email", json={
        "to": "recipient@example.com", 
        "subject": "Test", 
        "body": "Body"
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
