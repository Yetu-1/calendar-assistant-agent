from fastapi import FastAPI
from src.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Register the calendar assistant agent
    # TODO: Start the runtime (Start processing messages).
    yield
    # TODO: Stop the runtime (Stop processing messages).

app = FastAPI(lifespan=lifespan)