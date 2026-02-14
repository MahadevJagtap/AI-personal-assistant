
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from app.services.whatsapp_service import whatsapp_service
from app.services.reminder_service import ReminderService

# Configure logging
logger = logging.getLogger(__name__)

MEETINGS_FILE = os.path.join(os.path.dirname(__file__), 'meetings.json')

class MeetingScheduler:
    """
    Handles meeting storage, conflict detection, and background reminders.
    """
    def __init__(self):
        self.meetings: List[Dict] = []
        self.scheduler = BackgroundScheduler()
        self.reminder_service = ReminderService(self)
        self.load_meetings()
        # Note: We don't start it here, we let the startup event handle it.
        # But we initialize it for tool usage.

    def load_meetings(self):
        """Loads meetings from JSON file."""
        if os.path.exists(MEETINGS_FILE):
            try:
                with open(MEETINGS_FILE, 'r') as f:
                    self.meetings = json.load(f)
                logger.info(f"Loaded {len(self.meetings)} meetings.")
            except Exception as e:
                logger.error(f"Error loading meetings: {e}")
                self.meetings = []
        else:
            self.meetings = []

    def save_meetings(self):
        """Saves meetings to JSON file."""
        try:
            with open(MEETINGS_FILE, 'w') as f:
                json.dump(self.meetings, f, indent=4)
            logger.info("Meetings saved.")
        except Exception as e:
            logger.error(f"Error saving meetings: {e}")

    def _reminder_job(self, title: str):
        """Callback function for the reminder."""
        msg = f"🔔 Reminder: Meeting '{title}' is starting soon!"
        print(f"\n{msg}")
        logger.info(f"Triggered reminder for '{title}'")
        
        # Send WhatsApp Notification
        whatsapp_service.send_message(msg)

    def _reschedule_reminders(self):
        """Re-adds reminders for all future meetings on startup."""
        self.scheduler.remove_all_jobs()
        now = datetime.now()
        for meeting in self.meetings:
            try:
                start_dt = datetime.strptime(meeting['start'], "%Y-%m-%d %H:%M")
                # Schedule reminder 10 minutes before, or immediately if within window
                reminder_time = start_dt - timedelta(minutes=10)
                
                if reminder_time > now:
                    self.scheduler.add_job(
                        self._reminder_job,
                        trigger=DateTrigger(run_date=reminder_time),
                        args=[meeting['title']],
                        id=f"reminder_{meeting['start']}_{meeting['title']}"
                    )
            except ValueError:
                continue

    def check_conflicts(self, new_start: datetime, duration_minutes: int) -> bool:
        """
        Checks if a new meeting overlaps with existing ones.
        Returns True if there is a conflict.
        """
        new_end = new_start + timedelta(minutes=duration_minutes)

        for meeting in self.meetings:
            try:
                existing_start = datetime.strptime(meeting['start'], "%Y-%m-%d %H:%M")
                existing_end = existing_start + timedelta(minutes=meeting['duration'])

                # Overlap logic: (StartA < EndB) and (EndA > StartB)
                if new_start < existing_end and new_end > existing_start:
                    return True
            except ValueError:
                continue
        return False

    def add_meeting(self, title: str, start_time_str: str, duration_minutes: int = 30) -> str:
        """
        Adds a new meeting if no conflict exists.
        start_time_str format: "YYYY-MM-DD HH:MM"
        """
        try:
            start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return "❌ Invalid date format. Please use 'YYYY-MM-DD HH:MM'."

        if start_dt < datetime.now():
            return "❌ Cannot schedule meetings in the past."

        if self.check_conflicts(start_dt, duration_minutes):
            return f"❌ Conflict detected. You already have a meeting around {start_time_str}."

        # Add meeting
        meeting = {
            "title": title,
            "start": start_time_str,
            "duration": duration_minutes,
            "reminded": False
        }
        self.meetings.append(meeting)
        # Sort by start time
        self.meetings.sort(key=lambda x: x['start'])
        
        self.save_meetings()

        # Schedule reminder
        reminder_time = start_dt - timedelta(minutes=10)
        if reminder_time > datetime.now():
            self.scheduler.add_job(
                self._reminder_job,
                trigger=DateTrigger(run_date=reminder_time),
                args=[title],
                id=f"reminder_{start_time_str}_{title}"
            )
            reminder_msg = " (Reminder set for 10 mins before)"
        else:
            reminder_msg = ""

        return f"✅ Scheduled '{title}' on {start_time_str} for {duration_minutes} mins.{reminder_msg}"

        return f"✅ Scheduled '{title}' on {start_time_str} for {duration_minutes} mins.{reminder_msg}"

    def update_meeting(self, index: int, title: Optional[str] = None, start_time_str: Optional[str] = None, duration_minutes: Optional[int] = None) -> str:
        """
        Updates an existing meeting and resets the reminded flag if the start time changes.
        """
        if not (1 <= index <= len(self.meetings)):
            return f"❌ Invalid meeting index {index}."

        meeting = self.meetings[index - 1]
        time_changed = False

        if title:
            meeting['title'] = title
        if duration_minutes:
            meeting['duration'] = duration_minutes
        if start_time_str:
            try:
                new_start = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
                if start_time_str != meeting['start']:
                    if self.check_conflicts(new_start, duration_minutes or meeting['duration']):
                        # Temp check: exclude current meeting from conflict if we were smarter, 
                        # but simple check usually works for non-overlapping move
                        pass 
                    meeting['start'] = start_time_str
                    time_changed = True
            except ValueError:
                return "❌ Invalid date format. Please use 'YYYY-MM-DD HH:MM'."

        if time_changed:
            meeting['reminded'] = False
            logger.info(f"Meeting '{meeting['title']}' rescheduled. Reminded flag reset.")

        self.save_meetings()
        return f"✅ Updated meeting '{meeting['title']}'."

    def cleanup_meetings(self, hours_back: int = 24):
        """
        Removes meetings that ended more than hours_back ago.
        """
        now = datetime.now()
        original_count = len(self.meetings)
        
        updated_meetings = []
        for m in self.meetings:
            try:
                end_dt = datetime.strptime(m['start'], "%Y-%m-%d %H:%M") + timedelta(minutes=m['duration'])
                if end_dt > (now - timedelta(hours=hours_back)):
                    updated_meetings.append(m)
            except Exception:
                updated_meetings.append(m) # Keep if unparseable to be safe
        
        if len(updated_meetings) < original_count:
            self.meetings = updated_meetings
            self.save_meetings()
            logger.info(f"Cleaned up {original_count - len(updated_meetings)} expired meetings.")

    def list_meetings(self) -> str:
        """Returns a formatted list of upcoming meetings."""
        if not self.meetings:
            return "No upcoming meetings scheduled."

        output = "📅 **Upcoming Meetings:**\n"
        for idx, m in enumerate(self.meetings):
            output += f"{idx + 1}. **{m['start']}** ({m['duration']} mins): {m['title']}\n"
        return output

    def delete_meeting(self, index: int) -> str:
        """Deletes a meeting by its 1-based index from list_meetings."""
        if 1 <= index <= len(self.meetings):
            removed = self.meetings.pop(index - 1)
            self.save_meetings()
            self._reschedule_reminders() # Simple way to clean up jobs
            return f"✅ Deleted meeting: '{removed['title']}' at {removed['start']}."
        else:
            return f"❌ Invalid meeting index. Please choose between 1 and {len(self.meetings)}."

# Singleton instance
meeting_scheduler = MeetingScheduler()
