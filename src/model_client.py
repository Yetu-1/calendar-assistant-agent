from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.config import Settings

class ModelClientManagerMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class ModelClientManager(metaclass=ModelClientManagerMeta):
    def __init__(self) -> None:
        # Create the model client.
        self._client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=Settings.OPENAI_API_KEY,
        )
    async def close(self) -> None:
        await self._client.close()