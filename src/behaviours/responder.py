from abc import abstractmethod, ABCMeta
from typing import Optional

from spade.behaviour import CyclicBehaviour

from src.utils.acl_message import ACLMessage


class Responder(CyclicBehaviour, metaclass=ABCMeta):
    @abstractmethod
    def prepare_response(self, request: ACLMessage) -> ACLMessage:
        pass

    @abstractmethod
    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        pass

    async def receive(self, timeout: float = None) -> Optional[ACLMessage]:
        result = await super().receive(timeout)
        if result is not None:
            result.__class__ = ACLMessage
        return result
