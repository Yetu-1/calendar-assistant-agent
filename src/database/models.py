from sqlmodel import SQLModel, Field, Relationship
import uuid

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default=None, primary_key=True)
    username: str
    email: str
    token: str | None

class MessageBase(SQLModel):
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id")
    content: str
    source: str

class Message(MessageBase, table=True):
    id: int = Field(default=None, primary_key=True)    
    conversation: "Conversation" = Relationship(back_populates="messages")
    
class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    messages: list[Message] = Relationship(back_populates="conversation")