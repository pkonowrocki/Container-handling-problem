from abc import ABC
from typing import Optional

from spade.behaviour import CyclicBehaviour

from src.utils.acl_message import ACLMessage


class BaseCyclicBehaviour(CyclicBehaviour, ABC):
    async def receive(self, timeout: float = None) -> Optional[ACLMessage]:
        result = await super().receive(timeout)
        if result is not None:
            result.__class__ = ACLMessage
        return result
