from sqlmodel import select
from src.database.models import User, Message
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

