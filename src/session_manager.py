from src.database.db import Database
from src.database.models import Session, Message
import uuid
from uuid import UUID
from autogen_core.models import (
    LLMMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResultMessage,
    FunctionExecutionResult,
)
from sqlmodel import select

class SessionManagerMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class SessionManager(metaclass=SessionManagerMeta):
    def __init__(self) -> None:
        self._database = Database()
        self._system_message = ("You are a helpful Google Calendar Assistant that can (using tools):\n"
            "- Create google calendar events\n"
            "- Delete google calendar events\n"
            "- Fetch google calendar events and show the user\n"
            "- Reshecdule google calendar events\n"
            "--- Follow the Instructions below when interacting with the user:\n"
            "1. Always get the current date, time and timezone using the appropriate tool.\n"
            "2. If the user asks about their schedule, availability, or existing events for a date, call the appropriate tool with the timeMin and timeMax values (in ISO 8601 format)."
            "3. When adding an event to the calendar ask them the details of the event they want to add to their calendar including the title of the event, time it starts and how long it is.\n"
            "4. Always Show the event created to the user in readable form and ask for a confirmation of details. "
            "Also, display the event in the required Google Calendar event JSON format.\n"
            "5. Before adding an event to the calendar, always check the time slot in the calendar to ensure there are no conflicts."
            "If another event exists at the same time, inform the user and ask whether to proceed.\n"
            "6. When rescheduling events use the appropriate tool to first read and confirm the event exists. "
            "Then ask the user for confirmation before updating it.\n")

    async def create(self, user_id: UUID) -> str:
        # Store session data in the database
        session = self._database.create(Session(id=uuid.uuid4(), user_id=user_id))
        # Store system message in database as the frist message associated with the session
        self._database.create(Message(session_id=session.id, content=self._system_message, source="system"))
        return session.id.hex
    
    def get(self, id: UUID) -> Session:
        # Fetch Session data from database
        statement = select(Session).where(Session.id == id)
        session = self._database.get(statement)
        return session
    
    def attach_message(self, session_id: UUID, content: str, source: str): 
        # Store system message in the database
        self._database.create(Message(session_id=session_id, content=content, source=source))
    
    def get_messages(self, session_id: UUID) -> list[LLMMessage]:
        # Fetch conversation messages from database
        statement = select(Message.source, Message.content).where(Message.session_id == session_id)
        results = self._database.get_all(statement)

        # Construct message list
        messages_list = []
        for source, content in results:
            if source == 'user':
                messages_list.append(UserMessage(content=content, source='user'))
            elif source == 'assistant':
                messages_list.append(AssistantMessage(content=content, source='assistant_message'))
            elif source == 'tool_call_request':
                # Deserialize string back to list of python dictionaries 
                tool_call_request_dict = json.loads(content)
                tool_call_request_obj = [
                    FunctionCall(id=call["id"], arguments=call["arguments"], name=call["name"]) for call in tool_call_request_dict
                ]
                messages_list.append(AssistantMessage(content=tool_call_request_obj, source='assistant_message'))    
            elif source == 'tool_call_result':
                # Deserialize string back to list of python dictionaries 
                tool_call_results_dict = json.loads(content)
                tool_call_results_obj = [
                    FunctionExecutionResult(call_id=call["call_id"], content=call["content"], is_error=call["is_error"], name=call["name"]) for call in tool_call_results_dict
                ]
                messages_list.append(FunctionExecutionResultMessage(content=tool_call_results_obj))
            elif source == 'system':
                messages_list.append(SystemMessage(content=content))
        return messages_list
