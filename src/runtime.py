from autogen_core import AgentId, SingleThreadedAgentRuntime
from src.tools.messages import CustomMessage

class RuntimeManagerMeta(type):
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

class RuntimeManager(metaclass=RuntimeManagerMeta):
    def __init__(self) -> None:
        self._runtime = SingleThreadedAgentRuntime()
    
    def start(self) -> None:
        self._runtime.start()

    async def stop_when_idle(self) -> None:
        await self._runtime.stop_when_idle()

    async def send_message(self, message: CustomMessage, agent_id: AgentId) -> CustomMessage:
        response = await self._runtime.send_message(message, agent_id)
        return response
