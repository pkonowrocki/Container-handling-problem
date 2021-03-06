from abc import ABCMeta, abstractmethod
from enum import IntEnum
from typing import Optional

from src.behaviours.base_cyclic_behaviour import BaseCyclicBehaviour
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class RequestResponderState(IntEnum):
    WAITING_FOR_REQUEST = 0,
    REQUEST_AGREED = 1,
    FINALIZED = 2


class RequestResponder(BaseCyclicBehaviour, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self._state: RequestResponderState = RequestResponderState.WAITING_FOR_REQUEST
        self._request: Optional[ACLMessage] = None

    async def run(self):
        if self._state == RequestResponderState.WAITING_FOR_REQUEST:
            request: ACLMessage = await self.receive()
            if request is not None:
                self._request = request
                response: ACLMessage = await self.prepare_response(request)
                if response.performative == Performative.AGREE:
                    self._state = RequestResponderState.REQUEST_AGREED
                await self.send(response)
            return
        if self._state == RequestResponderState.REQUEST_AGREED:
            response: ACLMessage = await self.prepare_result_notification(self._request)
            await self.send(response)
            self._state = RequestResponderState.WAITING_FOR_REQUEST
            return

    @abstractmethod
    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        pass

    @abstractmethod
    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        pass
