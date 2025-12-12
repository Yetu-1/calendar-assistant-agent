from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, WebSocketException, status
from src.tools.messages import CustomMessage
from src.database.repository import UserRepository
from src.database.models import User
from sqlmodel import Session
from typing import List, Annotated
from autogen_core.tools import Tool
from src.agents.calendar_agent import CalendarAssistantAgent
from src.tools.calendar_api_client import CalendarAPIClient
import uuid
from src.runtime import RuntimeManager
from autogen_core import AgentId
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from src.auth import create_new_user, authenticate_user, validate_token

# Create a runtime.
runtime = RuntimeManager();

password_hash = PasswordHash.recommended()

# Websockets connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Server Running"}

@router.post("/login")
async def login( email: str, password: str):
    token = await authenticate_user(email, password)
    return {"jwt": token}


@router.post("/adduser")
async def add_user( username: str, email: str, password: str):
    user = User(id=uuid.uuid4(), username=username, email=email, password=password)
    return create_new_user(user)

async def get_token(
    websocket: WebSocket,
    token: Annotated[str | None, Query()] = None,
):
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return token

@router.websocket("/ws/")
async def websocket_endpoint( websocket: WebSocket):
    token = websocket.query_params.get("token")
    user_id, session_id = validate_token(token)
    users = UserRepository()
    # Fetch User data from database
    user = users.get(user_id)
    agent_id = AgentId(type="calendar_agent", key=f"calendar-agent-{user.id}-{session_id}")
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from websocket
            message =  CustomMessage(user_id=user.id, session_id=session_id, content=await websocket.receive_text())
            # Send the message to the calendar assistant agent
            response = await runtime.send_message(message, agent_id)
            await manager.send_message(f"Assistant: {response.content}", websocket)
    except WebSocketDisconnect:
        # TODO: Delete conversation from database
        # Disconnect websocket
        manager.disconnect(websocket)