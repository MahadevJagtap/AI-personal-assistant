
from fastapi.testclient import TestClient
from api.main import app
import os
import unittest
from unittest.mock import patch

client = TestClient(app)

class TestAPI(unittest.TestCase):
    def test_health(self):
        print("\n--- Testing GET /health ---")
        response = client.get("/health")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.json()}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        print("✅ Health check passed.")

    def test_meetings(self):
        print("\n--- Testing GET /meetings ---")
        response = client.get("/meetings")
        print(f"Status: {response.status_code}")
        # print(f"Body: {response.json()}") 
        self.assertEqual(response.status_code, 200)
        self.assertIn("formatted_text", response.json())
        print("✅ Meetings endpoint passed.")

    @patch('agent.email_service.email_service._connect_and_send')
    def test_email(self, mock_send):
        print("\n--- Testing POST /email ---")
        mock_send.return_value = True # Mock success
        
        payload = {
            "to": "test@example.com",
            "subject": "API Test",
            "body": "Hello from API"
        }
        response = client.post("/email", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.json()}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        print("✅ Email endpoint passed.")

    # Note: /chat invokes logic that might take time or fail if keys aren't set.
    # We'll skip deep chat test here or mock it if we wanted purely API layer test.
    # But let's try a simple one.
    @patch('api.main.run_agent')
    def test_chat_mock(self, mock_run):
        print("\n--- Testing POST /chat (Mocked Agent) ---")
        mock_run.return_value = "I am a mocked agent."
        
        response = client.post("/chat", json={"message": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "I am a mocked agent.")
        print("✅ Chat endpoint passed.")

if __name__ == "__main__":
    unittest.main()
