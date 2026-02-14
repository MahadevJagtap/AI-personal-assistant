
import pytest
import os
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app

# Fixture for API Client
@pytest.fixture
def client():
    return TestClient(app)

# Fixture to mock SMTP (Email)
@pytest.fixture(autouse=True)
def mock_smtp():
    with patch("agent.email_service.smtplib.SMTP") as mock:
        yield mock

# Fixture to use a temporary meetings file
@pytest.fixture(autouse=True)
def temp_meetings_file(tmp_path):
    # Create a temp file
    d = tmp_path / "data"
    d.mkdir()
    p = d / "test_meetings.json"
    p.write_text("[]") # Initialize empty list
    
    # Patch the MEETINGS_FILE constant in scheduler
    # Note: We need to patch where it's used or the object itself if possible.
    # Since agent.scheduler.MEETINGS_FILE is a global string, patching it might be tricky if it's already imported.
    # Better approach: Patch MeetingScheduler.meetings_file instance attribute if it exists, 
    # or patch the module level variable BEFORE app startup if possible.
    # Let's inspect scheduler.py... likely hardcoded.
    # If hardcoded, we might need to rely on 'agent.scheduler.MEETINGS_FILE' patch.
    
    # Patch the global constant if possible, but mainly the instance
    with patch("agent.scheduler.MEETINGS_FILE", str(p)):
        from agent.scheduler import meeting_scheduler
        # Reload/Reset the scheduler instance configuration
        meeting_scheduler.meetings_file = str(p)
        meeting_scheduler.meetings = [] 
        meeting_scheduler.save_meetings() # Ensure file exists standardly
        yield str(p)
        # Cleanup
        meeting_scheduler.meetings = []
