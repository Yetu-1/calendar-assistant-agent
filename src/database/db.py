from sqlmodel import create_engine, SQLModel, Session, select
from src.database.models import User, Conversation, Message
from uuid import UUID

DATABASE_URL = "sqlite:///db.sqlite"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def get_user(user_id: str, session: Session) -> User:
    # Fetch User data from database
    statement = select(User).where(User.id == UUID(user_id))
    results = session.exec(statement)
    user = results.first()
    return user

def get_conversation(conversation_id: str, session: Session) -> Conversation:
    # Fetch conversation data from database
    statement = select(Conversation).where(Conversation.id == UUID(conversation_id))
    results = session.exec(statement)
    conversation = results.first()
    return conversation

def get_messages(conversation_id: str, session: Session) -> list[Message]:
    # Fetch conversation messages from database
    statement = select(Message).where(Conversation.id == UUID(conversation_id))
    results = session.exec(statement)
    return results