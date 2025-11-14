from typing import List
from pydantic import BaseModel, Field

class Message(BaseModel):
    client_id: str | None = Field(None, description="Id of client")
    content: str