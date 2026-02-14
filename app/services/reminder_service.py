import logging
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.whatsapp_service import whatsapp_service
from app.agent.email_service import email_service
from app.config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Using Asia/Kolkata as requested
LOCAL_TZ = ZoneInfo("Asia/Kolkata")

class ReminderService:
    """
    Handles reminders for meetings across multiple channels with retry logic and timezone safety.
    """
    def __init__(self, scheduler_instance):
        self.scheduler = scheduler_instance
        self.config = Config
        self.offset_minutes = self.config.REMINDER_OFFSET_MINUTES
        
        logger.info(f"ReminderService initialized with {self.offset_minutes} minute offset.")

    def check_reminders(self):
        """
        Iterates through meetings and sends reminders if within the configured window.
        Triggered every minute by APScheduler.
        """
        now = datetime.now(LOCAL_TZ)
        logger.info(f"Checking reminders at {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        modified = False
        for meeting in self.scheduler.meetings:
            try:
                # Meetings are stored as "YYYY-MM-DD HH:MM" strings.
                # Use strptime then attach LOCAL_TZ
                naive_start = datetime.strptime(meeting['start'], "%Y-%m-%d %H:%M")
                start_dt = naive_start.replace(tzinfo=LOCAL_TZ)
                
                # Check for skipped meetings (Server Downtime case)
                # If meeting is in future or within 1 minute grace period but not reminded
                # Or if already passed but was recent? Let's stick to the 10-min window logic.
                
                reminder_time = start_dt - timedelta(minutes=self.offset_minutes)
                
                # Logic:
                # 1. If start_dt has passed more than a few minutes ago, mark as reminded=True silently (cleanup edge case)
                if now > (start_dt + timedelta(minutes=5)) and not meeting.get("reminded", False):
                    logger.info(f"Skipping past meeting: {meeting['title']} at {meeting['start']}")
                    meeting["reminded"] = True
                    modified = True
                    continue

                # 2. Trigger window: current time is at or past reminder_time and meeting hasn't started yet
                # OR it's currently starting (edge case restart).
                if now >= reminder_time and now <= start_dt and not meeting.get("reminded", False):
                    success = self._trigger_reminder(meeting)
                    if success:
                        meeting["reminded"] = True
                        modified = True
            except Exception as e:
                logger.error(f"Error checking reminder for meeting '{meeting.get('title')}': {e}")
                continue
        
        if modified:
            self.scheduler.save_meetings()

    def _trigger_reminder(self, meeting: dict) -> bool:
        """Sends notifications via multiple channels with simple retry logic."""
        title = meeting.get("title", "Meeting")
        start_str = meeting.get("start")
        
        message = f"🔔 **Meeting Reminder**\n\nYour meeting '{title}' is starting soon at {start_str} (in {self.offset_minutes} minutes)."
        
        logger.info(f"Triggering reminder for '{title}' at {start_str}")
        
        # 1. Send WhatsApp with 3 retries
        whatsapp_success = False
        for attempt in range(1, 4):
            res = whatsapp_service.send_message(message)
            if "✅" in res:
                logger.info(f"WhatsApp reminder sent for '{title}' (Attempt {attempt})")
                whatsapp_success = True
                break
            else:
                logger.warning(f"WhatsApp retry {attempt}/3 for '{title}': {res}")
                if attempt < 3:
                    time.sleep(1) # Small delay before retry

        # 2. Send Email with 1 retry
        email_success = False
        to_email = self.config.EMAIL_ADDRESS
        if to_email:
            for attempt in range(1, 3):
                subject = f"🔔 Reminder: {title} starting soon"
                res = email_service.send_email(to_email, subject, message)
                if "✅" in res:
                    logger.info(f"Email reminder sent for '{title}' to {to_email} (Attempt {attempt})")
                    email_success = True
                    break
                else:
                    logger.warning(f"Email retry {attempt}/2 for '{title}': {res}")

        # Return True if at least one channel succeeded (or both as per business logic)
        # We'll mark as reminded if we tried our best.
        return True
