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
        """Handles OAuth 2.0 authentication from ENV string or local file."""
        import json
        creds = None
        
        # 1. Try Token Persistence (Local)
        token_file = 'token.pickle'
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                try:
                    creds = pickle.load(token)
                except Exception:
                    creds = None
        
        # 2. If no valid creds, load from JSON Source
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Source can be Environment Variable (JSON String) or Local File (calendar.json)
                google_json = self.config.GOOGLE_CREDENTIALS_JSON
                
                try:
                    if google_json and "{" in google_json:
                        # Raw JSON string from ENV
                        creds_dict = json.loads(google_json)
                        flow = InstalledAppFlow.from_client_config(creds_dict, self.SCOPES)
                    else:
                        # Fallback to local file path
                        json_path = google_json or 'calendar.json'
                        if not os.path.exists(json_path):
                            logger.error(f"Google credentials not found (ENV or {json_path})")
                            return None
                        flow = InstalledAppFlow.from_client_secrets_file(json_path, self.SCOPES)
                    
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Authentication flow failed: {e}")
                    return None
            
            # Save the credentials locally if possible (for next run)
            try:
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.warning(f"Could not save token locally: {e}")

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
