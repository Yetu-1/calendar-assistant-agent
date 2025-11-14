from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect

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
            # TODO: Receive message from websocket
            message = await websocket.receive_text()
            # TODO: Send the message to the calendar assistant agent.
    except WebSocketDisconnect:
        # Disconnect websocket
        manager.disconnect(websocket)