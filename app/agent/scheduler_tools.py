from datetime import datetime
from langchain.tools import tool
from app.scheduler import meeting_scheduler
from app.services.whatsapp_service import whatsapp_service

@tool
def schedule_meeting(text: str) -> str:
    """
    Schedules a meeting. Input text should clarify title, date, time, and duration.
    Expected format in text for simplicity (or extracted by agent before calling):
    "YYYY-MM-DD HH:MM|Title|Duration"
    
    Example: "2023-10-27 15:00|Projects Sync|30"
    
    If the agent cannot determine exact date/time, it should ask the user first.
    """
    try:
        # Simple parsing for the tool prototype. 
        # In a real agent, the LLM extracts args and calls this with structure, 
        # or we parse a delimiter-separated string.
        parts = text.split('|')
        if len(parts) < 2:
            return "❌ Please provide details in format: 'YYYY-MM-DD HH:MM|Title|Duration(opt)'"
        
        start_str = parts[0].strip()
        title = parts[1].strip()
        duration = int(parts[2].strip()) if len(parts) > 2 else 30
        
        res = meeting_scheduler.add_meeting(title, start_str, duration)
        
        if res.startswith("✅"):
            whatsapp_service.send_message(f"📅 Meeting Scheduled: {title}\nTime: {start_str}\nDuration: {duration} mins")
            
        return res
    except Exception as e:
        return f"❌ Error processing request: {e}"

@tool
def list_meetings() -> str:
    """
    Lists all upcoming scheduled meetings.
    """
    return meeting_scheduler.list_meetings()

@tool
def delete_meeting(index_str: str) -> str:
    """
    Deletes a meeting by its index number (retrieved from list_meetings).
    Input should be a simple integer string, e.g., "1".
    """
    try:
        index = int(index_str.strip())
        return meeting_scheduler.delete_meeting(index)
    except ValueError:
        return "❌ Invalid index format. Please provide an integer."
