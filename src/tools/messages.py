from typing import List
from pydantic import BaseModel, Field
from uuid import UUID

class CustomMessage(BaseModel):
    user_id: UUID | None = Field(None, description="Id of the user")
    conversation_id: UUID | None = Field(None, description="Id of the coversation")
    content: str

class EventDateTime(BaseModel):
    dateTime: str = Field(..., description="Event datetime string in ISO 8601 format")
    timeZone: str = Field(None, description="timezone of event") #. tbd - Make this required.

class CalendarEvent(BaseModel):
    summary: str = Field(..., description="Short title for the event")
    location: str | None = Field(None, description="Location of the event")
    description: str | None = Field(None, description="Description of the event")
    start: EventDateTime
    end: EventDateTime 
    recurrence: List[str] | None = Field(None, description=("Recurrence rules (RRULE)"))