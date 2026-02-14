from datetime import datetime, timedelta
from langchain_core.tools import tool
from app.services.google_calendar_service import calendar_service
from app.services.whatsapp_service import whatsapp_service
from app.scheduler import meeting_scheduler # For reminder integration

@tool
def calendar_tool(action: str, details: str) -> str:
    """
    Manages Google Calendar events.
    
    Actions:
    - 'create': Create a new event. Details: 'Summary|YYYY-MM-DD HH:MM|DurationInMinutes'
    - 'list': List upcoming events. Details: Ignored.
    - 'update': Update an event. Details: 'EventID|NewSummary|NewStart|Duration' (send 'None' to skip a field)
    - 'delete': Delete an event. Details: 'EventID'
    """
    try:
        if action == 'create':
            parts = details.split('|')
            if len(parts) < 2:
                return "❌ Format: 'Summary|YYYY-MM-DD HH:MM|Duration(opt)'"
            summary = parts[0].strip()
            start_time = parts[1].strip()
            duration = int(parts[2].strip()) if len(parts) > 2 else 30
            
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.strftime("%Y-%m-%d %H:%M")
            
            res = calendar_service.create_event(summary, start_time, end_time)
            
            if res.startswith("✅"):
                # Trigger WhatsApp Notification
                notification_msg = f"🗓️ Google Calendar: Event Created!\nSummary: {summary}\nTime: {start_time}"
                whatsapp_service.send_message(notification_msg)
                
                # Optionally add to APScheduler for reminder (e.g. 10 mins before)
                # We can reuse meeting_scheduler logic if compatible
                reminder_time = start_dt - timedelta(minutes=10)
                if reminder_time > datetime.now():
                    meeting_scheduler.scheduler.add_job(
                        lambda: whatsapp_service.send_message(f"🔔 Reminder: '{summary}' is starting in 10 mins!"),
                        'date',
                        run_date=reminder_time,
                        id=f"gcal_reminder_{start_time}_{summary}"
                    )
            return res

        elif action == 'list':
            events = calendar_service.get_upcoming_events()
            if not events:
                return "No upcoming events found."
            
            res = "📅 **Upcoming Calendar Events:**\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                res += f"- {start}: {event.get('summary')} (ID: {event.get('id')})\n"
            return res

        elif action == 'update':
            parts = details.split('|')
            if len(parts) < 1:
                return "❌ Format: 'EventID|NewSummary|NewStart|Duration'"
            event_id = parts[0].strip()
            new_summary = parts[1].strip() if len(parts) > 1 and parts[1].lower() != 'none' else None
            new_start = parts[2].strip() if len(parts) > 2 and parts[2].lower() != 'none' else None
            new_duration = int(parts[3].strip()) if len(parts) > 3 and parts[3].lower() != 'none' else None
            
            new_end = None
            if new_start and new_duration:
                start_dt = datetime.strptime(new_start, "%Y-%m-%d %H:%M")
                end_dt = start_dt + timedelta(minutes=new_duration)
                new_end = end_dt.strftime("%Y-%m-%d %H:%M")
            
            return calendar_service.update_event(event_id, new_summary, new_start, new_end)

        elif action == 'delete':
            return calendar_service.delete_event(details.strip())

        else:
            return "❌ Unknown action. Use 'create', 'list', 'update', or 'delete'."

    except Exception as e:
        return f"❌ Error: {e}"
