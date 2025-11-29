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
from src.database.models import Message, Conversation
from src.database.repository import UserRepository, ConversationRepository, MessageRepository

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
        self._conversations = ConversationRepository()
        self._messages = MessageRepository()
        self._users = UserRepository() 

    @message_handler
    async def handle_user_message(self, message: CustomMessage, ctx: MessageContext) -> CustomMessage:
        # Check if conversation already exists in the database
        conversation = self._conversations.get(message.conversation_id)
        if not conversation: 
            # Store conversation data in the database
            self._conversations.create(Conversation(id=message.conversation_id, user_id=message.user_id))
            # Store system message in database
            self._messages.create(Message(conversation_id=message.conversation_id, content=self._system_messages[0].content, source="system"))

        # Store user message in the database
        self._messages.create(Message(conversation_id=message.conversation_id, content=message.content, source="user"))

        while True:
            # Get messages from the database to give llm context
            messages = self._messages.get_all(message.conversation_id,)
            # Run the chat completion with the tools.
            llm_result = await self._model_client.create(
                messages=messages,
                tools=self._tools,
                cancellation_token=ctx.cancellation_token,
            )

            print(f"{'-'*80}\n{self.id.type}:\n{llm_result.content}", flush=True)
            # If there are no tool calls, return the result.
            if isinstance(llm_result.content, str):
                # Save the llm's result to the database.
                self._messages.create(Message(conversation_id=message.conversation_id, content=llm_result.content, source="assistant_message"))
                return CustomMessage(content=llm_result.content)
            try:
                # Save Function call in the database
                tool_call_request = json.dumps([ # Serialize tool call request to string
                    {
                        "name": call.name,
                        "id": call.id,
                        "arguments": call.arguments,
                    }
                    for call in llm_result.content
                ])
                # Save tool call request message in the database
                self._messages.create(Message(conversation_id=message.conversation_id, content=tool_call_request, source="tool_call_request"))

                # Execute the tool calls.
                tool_call_results = await asyncio.gather(
                    *[self._execute_tool_call(call, ctx.cancellation_token) for call in llm_result.content]
                )
                # Serialize tool call result to string
                tool_call_results_serialized = json.dumps([
                    {
                        "name": call.name,
                        "call_id": call.call_id,
                        "content": call.content,
                        "is_error": call.is_error,
                    }
                    for call in tool_call_results
                ])

                print(f"{'-'*80}\n{self.id.type}:\n{tool_call_results}", flush=True)

                # Save the function execution results in the database.
                self._messages.create(Message(conversation_id=message.conversation_id, content=tool_call_results_serialized, source="tool_call_result"))
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