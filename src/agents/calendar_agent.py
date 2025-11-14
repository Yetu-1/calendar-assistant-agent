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
from src.tools.messages import Message

sessions: Dict[str, List[LLMMessage]] = {}

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
    async def handle_user_message(self, message: Message, ctx: MessageContext) -> Message:
        # Create a session of messages.
        if message.client_id not in sessions:
            sessions[message.client_id] = []
            sessions[message.client_id].append(self._system_messages[0]) # Append the system message

        sessions[message.client_id].append(UserMessage(content=message.content, source="user"))

        while True:
            # Run the chat completion with the tools.
            llm_result = await self._model_client.create(
                messages=sessions[message.client_id],
                tools=self._tools,
                cancellation_token=ctx.cancellation_token,
            )

            # Add the first model create result to the session.
            sessions[message.client_id].append(AssistantMessage(content=llm_result.content, source="assistant"))

            print(f"{'-'*80}\n{self.id.type}:\n{llm_result.content}", flush=True)
            # If there are no tool calls, return the result.
            if isinstance(llm_result.content, str):
                return Message(content=llm_result.content)
            assert isinstance(llm_result.content, list) and all(
                isinstance(call, FunctionCall) for call in llm_result.content
            )

            # Execute the tool calls.
            tool_call_results = await asyncio.gather(
                *[self._execute_tool_call(call, ctx.cancellation_token) for call in llm_result.content]
            )
            print(f"{'-'*80}\n{self.id.type}:\n{tool_call_results}", flush=True)

            # Add the function execution results to the session.
            sessions[message.client_id].append(FunctionExecutionResultMessage(content=tool_call_results))    

    async def _execute_tool_call(
        self, call: FunctionCall, cancellation_token: CancellationToken
    ) -> FunctionExecutionResult:
        # Find the tool by name.
        tool = next((tool for tool in self._tools if tool.name == call.name), None)
        assert tool is not None

        # Run the tool and capture the result.
        try:
            arguments = json.loads(call.arguments)
            result = await tool.run_json(arguments, cancellation_token)
            return FunctionExecutionResult(
                call_id=call.id, content=tool.return_value_as_string(result), is_error=False, name=tool.name
            )
        except Exception as e:
            return FunctionExecutionResult(call_id=call.id, content=str(e), is_error=True, name=tool.name)