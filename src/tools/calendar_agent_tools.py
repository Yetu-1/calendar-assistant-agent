from autogen_core.tools import FunctionTool
from src.tools.messages import CalendarEvent, EventDateTime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from autogen_core.tools import Tool
from src.config import Settings
from datetime import datetime
from pathlib import Path
from typing import List
import tzlocal

# Path to the service account JSON file for Google API authentication. 
service_account_file_path = Path(__file__).parent / "service_account.json"

class CalendarClient: 
    def __init__(self):
        # Initialize the Google Calendar API client with service account credentials
        self.service = build("calendar", "v3", 
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file_path,
                scopes=["https://www.googleapis.com/auth/calendar"]
            )
        )

def get_date_and_time() -> str:
    time_zone = tzlocal.get_localzone() # Detect system timezone
    date_and_time = datetime.now(time_zone) 
    return (
        f"Today's date and time: {date_and_time}.\n"
        f"TIME ZONE: {time_zone}.\n"
        f"Today's day of the week: {date_and_time.strftime('%A')}"
    )

def add_event_to_calendar(event: CalendarEvent) -> str:
    client = CalendarClient();
    result = client.service.events().insert(
        calendarId=Settings.CALENDAR_ID, body=event.model_dump()  # Converts Pydantic model to dict
    ).execute()
    return f"Result: {result}"

get_datetime_tool = FunctionTool(get_date_and_time, description="Use this tool to fetch current date and time.")
add_event_to_calendar_tool = FunctionTool(
    add_event_to_calendar, description="Use to add event to calendar."
)