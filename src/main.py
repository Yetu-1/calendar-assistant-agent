from fastapi import FastAPI
from src.routes import router, runtime
from contextlib import asynccontextmanager
from src.config import Settings
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.agents.calendar_agent import CalendarAssistantAgent
from src.tools.calendar_agent_tools import calendar_agent_tools
from src.database.db import init_db
from src.database.models import User, Conversation, Message

# Create the model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=Settings.OPENAI_API_KEY,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    #init_db();
    # Register the calendar assistant agent
    await CalendarAssistantAgent.register(
        runtime,
        "calendar_assistant_agent",
        lambda: CalendarAssistantAgent(
            model_client=model_client,
            tool_schema=calendar_agent_tools,
        ),
    )
    # Start the runtime (Start processing messages).
    runtime.start()
    yield
    # Stop the runtime (Stop processing messages).
    await runtime.stop_when_idle()
    await model_client.close() # close the model client session

app = FastAPI(lifespan=lifespan)
app.include_router(router)
