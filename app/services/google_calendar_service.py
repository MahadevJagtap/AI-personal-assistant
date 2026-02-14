import os
import pickle
import logging
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configure logging
logger = logging.getLogger(__name__)

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        from app.config import Config
        self.config = Config
        self.service = self._authenticate()

    def _authenticate(self):
        """Handles OAuth 2.0 authentication without mandatory disk persistence."""
        import json
        from google.oauth2.credentials import Credentials
        
        creds = None
        google_json = self.config.GOOGLE_CREDENTIALS_JSON
        
        # 1. Attempt to use environment-based credentials first
        if google_json:
            try:
                creds_dict = json.loads(google_json)
                # If the string is a serialized token, load it directly
                if "token" in creds_dict:
                    creds = Credentials.from_authorized_user_info(creds_dict, self.SCOPES)
                else:
                    # If it's a client secret file, run the flow
                    flow = InstalledAppFlow.from_client_config(creds_dict, self.SCOPES)
                    # For automated cloud environments, a Refresh Token is better.
                    # run_local_server is for dev; cloud usually uses pre-authorized tokens.
                    creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Failed to authenticate from GOOGLE_CREDENTIALS_JSON: {e}")

        # 2. Local Fallback (for development)
        if not creds:
            token_file = 'token.pickle'
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    try:
                        creds = pickle.load(token)
                    except Exception:
                        creds = None
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists('calendar.json'):
                        flow = InstalledAppFlow.from_client_secrets_file('calendar.json', self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        logger.error("No valid Google Calendar credentials found (ENV or local).")
                        return None

        try:
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Error building calendar service: {e}")
            return None

    def check_conflict(self, start_time: str, end_time: str) -> bool:
        """
        Checks if the provided time range conflicts with existing events.
        start_time, end_time: ISO format strings
        """
        if not self.service: return False
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            events = events_result.get('items', [])
            return len(events) > 0
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
            return False

    def create_event(self, summary: str, start_time: str, end_time: str, description: str = "") -> str:
        """
        Creates a new event on the primary calendar.
        start_time, end_time: "YYYY-MM-DD HH:MM" format
        """
        if not self.service: return "❌ Calendar service not initialized."
        
        try:
            # Convert to ISO format for Google API
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
            
            start_iso = start_dt.isoformat() + 'Z' # 'Z' indicates UTC time
            end_iso = end_dt.isoformat() + 'Z'
            
            if self.check_conflict(start_iso, end_iso):
                return f"❌ Conflict detected for {start_time}. Another event exists."

            event = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start_iso, 'timeZone': 'UTC'},
                'end': {'dateTime': end_iso, 'timeZone': 'UTC'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return f"✅ Event created: {summary} at {start_time}. ID: {event.get('id')}"
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return f"❌ Error: {e}"

    def get_upcoming_events(self, limit: int = 5) -> list:
        """Returns a list of upcoming events."""
        if not self.service: return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=limit, singleEvents=True,
                orderBy='startTime').execute()
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    def update_event(self, event_id: str, new_summary=None, new_start=None, new_end=None) -> str:
        """Updates an existing event."""
        if not self.service: return "❌ Calendar service not initialized."
        
        try:
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            if new_summary: event['summary'] = new_summary
            if new_start:
                start_dt = datetime.strptime(new_start, "%Y-%m-%d %H:%M")
                event['start'] = {'dateTime': start_dt.isoformat() + 'Z', 'timeZone': 'UTC'}
            if new_end:
                end_dt = datetime.strptime(new_end, "%Y-%m-%d %H:%M")
                event['end'] = {'dateTime': end_dt.isoformat() + 'Z', 'timeZone': 'UTC'}
            
            updated_event = self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            return f"✅ Event updated: {updated_event.get('summary')}"
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return f"❌ Error: {e}"

    def delete_event(self, event_id: str) -> str:
        """Deletes an event by ID."""
        if not self.service: return "❌ Calendar service not initialized."
        
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return "✅ Event deleted successfully."
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return f"❌ Error: {e}"

# Singleton instance for general use
# (Note: Authentication will trigger on first initialization)
calendar_service = GoogleCalendarService()
