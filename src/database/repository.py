from sqlmodel import select
from src.database.models import User, Conversation, Message
from autogen_core.models import (
    LLMMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResultMessage,
    FunctionExecutionResult,
)
from autogen_core import FunctionCall
from uuid import UUID   
import json
from src.database.db import Database

class UserRepository:
    def __init__(self):
        self.database = Database()

    def create(self, user: User) -> str:
        self.database.create(user)

    def get(self, id: str) -> User:
        # Fetch User data from database
        statement = select(User).where(User.id == UUID(id))
        user = self.database.get(statement)
        return user

    def get_user_by_email(self, email: str) -> User:
        # Fetch User data from database
        statement = select(User).where(User.email == email)
        user = self.database.get(statement)
        return user

    def delete(self, id: str):
        statement = select(User).where(User.id == UUID(id))
        self.database.delete(statement)
   

class ConversationRepository:
    def __init__(self):
        self.database = Database()

    def create(self, conversation: Conversation) -> str:
        self.database.create(conversation)

    def get(self, id: UUID) -> Conversation:
        # Fetch conversation data from database
        statement = select(Conversation).where(Conversation.id == id)
        user = self.database.get(statement)
        return user

    def delete(self, id: UUID):
        statement = select(Conversation).where(Conversation.id == id)
        self.database.delete(statement)

class MessageRepository:
    def __init__(self):
        self.database = Database()

    def create(self, message: Message) -> str:
        self.database.create(message)

    def get_all(self, conversation_id: UUID) -> list[LLMMessage]:
        # Fetch conversation messages from database
        statement = select(Message.source, Message.content).where(Message.conversation_id == conversation_id)
        results = self.database.get_all(statement)

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

