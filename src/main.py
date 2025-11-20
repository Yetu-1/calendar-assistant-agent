from fastapi import FastAPI
from src.routes import router, runtime
from contextlib import asynccontextmanager
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.database.models import User, Conversation, Message

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the runtime (Start processing messages).
    runtime.start()
    yield
    # Stop the runtime (Stop processing messages).
    await runtime.stop_when_idle()
    await model_client.close() # close the model client session

app = FastAPI(lifespan=lifespan)
app.include_router(router)
