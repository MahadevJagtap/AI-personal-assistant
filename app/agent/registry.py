from typing import List
from langchain.tools import BaseTool

# Import tools
from app.agent.scheduler_tools import schedule_meeting, list_meetings, delete_meeting
from app.agent.email_tools import send_email_tool
from app.tools.calendar_tool import calendar_tool

# Define the list of all available tools
ALL_TOOLS = [
    schedule_meeting,
    list_meetings,
    delete_meeting,
    send_email_tool,
    calendar_tool
]

def get_all_tools() -> List[BaseTool]:
    """Returns the list of all tools available to the agent."""
    return ALL_TOOLS
