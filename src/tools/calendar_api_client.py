from autogen_core.tools import FunctionTool
from src.tools.messages import CalendarEvent, EventDateTime, UserData
from googleapiclient.discovery import build
from google.oauth2 import service_account
from autogen_core.tools import Tool
from src.config import SETTINGS
from datetime import datetime
from pathlib import Path
from typing import List
import tzlocal

# Path to the service account JSON file for Google API authentication. 
service_account_file_path = Path(__file__).parent / "service_account.json"

class CalendarAPIClient: 
    def __init__(self, user_data: UserData=None):
        # TODO: use user data to build api client using token after oauth flow has been setup(for now use service account)

        # Initialize the Google Calendar API client with service account credentials
        self.service = build("calendar", "v3", 
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file_path,
                scopes=["https://www.googleapis.com/auth/calendar"]
            )
        )

    def get_date_and_time(self) -> str:
        time_zone = tzlocal.get_localzone() # Detect system timezone
        date_and_time = datetime.now(time_zone) 
        return (
            f"Today's date and time: {date_and_time}.\n"
            f"TIME ZONE: {time_zone}.\n"
            f"Today's day of the week: {date_and_time.strftime('%A')}"
        )

    def add_event_to_calendar(self, event: CalendarEvent) -> str:
        result = self.service.events().insert(
            calendarId=SETTINGS.calendar_id, body=event.model_dump()  # Converts Pydantic model to dict
        ).execute()
        return f"Result: {result}"

    def fetch_events(self, time_min: EventDateTime, time_max: EventDateTime) -> str:
        events_list = self.service.events().list(
                calendarId=SETTINGS.calendar_id,
                timeMin=time_min.dateTime,
                timeMax=time_max.dateTime,
                timeZone=time_min.timeZone,
                singleEvents=True,
                orderBy="startTime"
        ).execute()
        if not events_list:
            return "No events found in this time range."
        events = events_list.get("items", [])
        return f"Events:\n {events}"

    def patch_event(self, event_id: str, start: EventDateTime, end: EventDateTime) -> str:
        result = self.service.events().patch(
                calendarId=SETTINGS.calendar_id,
                eventId=event_id,
                body={
                    "start": start.model_dump(),  # Converts Pydantic model to dict
                    "end": end.model_dump(),   
                }
        ).execute()
        return f"Result: {result}"

    def delete_event(self, event_id: str) -> str:
        result = self.service.events().delete(
                calendarId=SETTINGS.calendar_id,
                eventId=event_id,
        ).execute()
        return f"Result: {result}"
    
    def get_tools(self) -> List[Tool]:
        tools = [
            FunctionTool(self.get_date_and_time, description="Use this tool to fetch current date and time."),
            FunctionTool(self.add_event_to_calendar, description="Use to add event to calendar."),
            FunctionTool(self.fetch_events, description="Use this tool to fetch events from the calendar."),
            FunctionTool(self.patch_event, description="Use the tool to reschedule and update event in the calendar."),
            FunctionTool(self.delete_event, description="Use this to to delete events in the calendar")
        ]
        return tools
