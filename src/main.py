from fastapi import FastAPI
from src.routes import router, runtime
from contextlib import asynccontextmanager
from src.runtime import RuntimeManager

runtime = RuntimeManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the runtime (Start processing messages).
    runtime.start()
    yield
    # Stop the runtime (Stop processing messages).
    await runtime.stop_when_idle()

app = FastAPI(lifespan=lifespan)
app.include_router(router)
