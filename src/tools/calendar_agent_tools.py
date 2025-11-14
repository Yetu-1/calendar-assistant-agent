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
