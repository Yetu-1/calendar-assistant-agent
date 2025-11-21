from sqlmodel import create_engine, SQLModel, Session, select
from src.database.models import User, Conversation, Message
from src.tools.messages import CustomMessage
from autogen_core.models import (
    LLMMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    FunctionExecutionResultMessage,
)
from uuid import UUID   

# TODO: make this url an environment variable 
DATABASE_URL = "sqlite:///src/database/db.sqlite"

class DatabaseManagerMeta(type):
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

class DatabaseManager(metaclass=DatabaseManagerMeta):
    def __init__(self) -> None:
        self._engine = create_engine(DATABASE_URL, echo=True)

    def get_user(self, user_id: str) -> User:
        # Fetch User data from database
        with Session(self._engine) as session:
            statement = select(User).where(User.id == UUID(user_id))
            results = session.exec(statement)
            user = results.first()
            return user

    def get_conversation(self, conversation_id: UUID, session : Session) -> Conversation:
        # Fetch conversation data from database
        statement = select(Conversation).where(Conversation.id == conversation_id)
        results = session.exec(statement)
        conversation = results.first()
        return conversation

    def start_conversation(self, message: CustomMessage, system_message: str, session: Session):
        # Check if conversation already exists in the database
        conversation = self.get_conversation(message.conversation_id, session)
        if not conversation: 
            # Store conversation data in the database
            conversation = Conversation(id=message.conversation_id, user_id=message.user_id)
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            # Store system message in database
            sys_msg = Message(conversation_id=message.conversation_id, content=system_message, source="system")
            self.save_message(sys_msg, session)
            session.add(sys_msg)
            session.commit()

        return conversation
    
    def save_message(self, message: Message, session: Session) -> None:
        # Store system message in database
        session.add(message)
        session.commit()

    def get_messages(self, conversation_id: UUID, session: Session) -> list[LLMMessage]:
        # Fetch conversation messages from database
        statement = select(Message.source, Message.content).where(Message.conversation_id == conversation_id)
        results = session.exec(statement)

        # Construct message list
        messages_list = []
        for source, content in results:
            if source == 'user':
                messages_list.append(UserMessage(content=content, source='user'))
            elif source == 'assistant':
                messages_list.append(AssistantMessage(content=content, source='assistant'))
            elif source == 'tool_call':
                messages_list.append(FunctionExecutionResultMessage(content=content))
            elif source == 'system':
                messages_list.append(SystemMessage(content=content))
        return messages_list