from abc import abstractmethod
from typing import Optional

from spade.behaviour import CyclicBehaviour

from src.utils.acl_message import ACLMessage


class BaseCyclicBehaviour(CyclicBehaviour):
    @abstractmethod
    async def run(self):
        pass

    def __init__(self):
        super().__init__()

    async def receive(self, timeout: float = None) -> Optional[ACLMessage]:
        result = await super().receive(timeout)
        if result is not None:
            result.__class__ = ACLMessage
        return result
