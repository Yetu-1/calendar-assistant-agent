from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from autogen_core import AgentId, SingleThreadedAgentRuntime
from src.tools.messages import Message

# Create a runtime.
runtime = SingleThreadedAgentRuntime()
calendar_assistant_agent = AgentId("calendar_assistant_agent", "default") # define calendar agent ID

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

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from websocket
            message =  Message(client_id=client_id, content=await websocket.receive_text())
            # Send the message to the calendar assistant agent
            response = await runtime.send_message(message, calendar_assistant_agent)
            await manager.send_message(f"Assistant: {response.content}", websocket)
    except WebSocketDisconnect:
        # Disconnect websocket
        manager.disconnect(websocket)