import json
from typing import List, Dict
import asyncio
from autogen_core import (
    FunctionCall,
    MessageContext,
    RoutedAgent,
    message_handler,
    CancellationToken,
)
from autogen_core.models import (
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
)
from autogen_core.tools import Tool
from src.tools.messages import CustomMessage
from sqlmodel import Session
from src.database.db import DatabaseManager
from src.database.models import Message

class CalendarAssistantAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, tool_schema: List[Tool]) -> None:
        super().__init__("An calendar assistant agent.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(content="You are a helpful Google Calendar Assistant that can (using tools):\n"
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
                "Then ask the user for confirmation before updating it.\n"
            )
        ]
        self._model_client = model_client
        self._tools = tool_schema

    @message_handler
    async def handle_user_message(self, message: CustomMessage, ctx: MessageContext) -> CustomMessage:
        database = DatabaseManager()
        with Session(database._engine) as session:
            # Store conversation data and system message in the database if they do not already exist
            conversation = database.start_conversation(message, self._system_messages[0].content, session)
            # Store user message in the database
            database.save_message(Message(conversation_id=message.conversation_id, content=message.content, source="user"), session);

            while True:
                # Get messages from the database to give llm context
                messages = database.get_messages(message.conversation_id, session)

                # Run the chat completion with the tools.
                llm_result = await self._model_client.create(
                    messages=messages,
                    tools=self._tools,
                    cancellation_token=ctx.cancellation_token,
                )

                # Add the llm's result to the database.
                database.save_message(Message(conversation_id=message.conversation_id, content=llm_result.content, source="assistant"), session);

                print(f"{'-'*80}\n{self.id.type}:\n{llm_result.content}", flush=True)
                # If there are no tool calls, return the result.
                if isinstance(llm_result.content, str):
                    return CustomMessage(content=llm_result.content)

                try:
                    # Execute the tool calls.
                    tool_call_results = await asyncio.gather(
                        *[self._execute_tool_call(call, ctx.cancellation_token) for call in llm_result.content]
                    )
                    print(f"{'-'*80}\n{self.id.type}:\n{tool_call_results}", flush=True)

                    # Add the function execution results to the database.
                    database.save_message(Message(conversation_id=message.conversation_id, content=tool_call_results, source="tool_call"), session);   
                except Exception as e:
                    return Message(content=str(e))   

    async def _execute_tool_call(
        self, call: FunctionCall, cancellation_token: CancellationToken
    ) -> FunctionExecutionResult:
        # Find the tool by name.
        tool = next((tool for tool in self._tools if tool.name == call.name), None)
        # Check if tool is none 
        if tool is None:
            return FunctionExecutionResult(call_id=call.id, content="Unknown tool", is_error=True, name=call.name)

        # Run the tool and capture the result.
        try:
            arguments = json.loads(call.arguments)
            result = await tool.run_json(arguments, cancellation_token)
            return FunctionExecutionResult(
                call_id=call.id, content=tool.return_value_as_string(result), is_error=False, name=tool.name
            )
        except Exception as e:
            return FunctionExecutionResult(call_id=call.id, content=str(e), is_error=True, name=tool.name)