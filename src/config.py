import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    openai_api_key: str
    calendar_id: str

    model_config = SettingsConfigDict(env_prefix="MY_")


settings = Settings()