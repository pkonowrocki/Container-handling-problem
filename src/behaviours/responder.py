from abc import abstractmethod, ABCMeta

from spade.behaviour import CyclicBehaviour
from spade.message import Message


class Responder(CyclicBehaviour, metaclass=ABCMeta):
    @abstractmethod
    def prepare_response(self, request: Message) -> Message:
        pass

    @abstractmethod
    async def prepare_result_notification(self, request: Message) -> Message:
        pass
