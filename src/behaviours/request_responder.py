from abc import abstractmethod
from enum import IntEnum
from typing import Optional

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from src.utils.message_utils import get_performative
from src.utils.performative import Performative


class RequestResponderState(IntEnum):
    WAITING_FOR_REQUEST = 0,
    REQUEST_AGREED = 1,
    FINALIZED = 2


class RequestResponder(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self._state: RequestResponderState = RequestResponderState.WAITING_FOR_REQUEST
        self._request: Optional[Message] = None

    async def run(self):
        if self._state == RequestResponderState.WAITING_FOR_REQUEST:
            request: Message = await self.receive()
            if request is not None:
                self._request = request
                response: Message = self.prepare_response(request)
                if get_performative(response) == Performative.AGREE:
                    self._state = RequestResponderState.REQUEST_AGREED
                else:
                    self._state = RequestResponderState.WAITING_FOR_REQUEST
                await self.send(response)
            return
        if self._state == RequestResponderState.REQUEST_AGREED:
            response: Message = await self.prepare_result_notification(self._request)
            await self.send(response)
            self._state = RequestResponderState.WAITING_FOR_REQUEST
            return

    @abstractmethod
    def prepare_response(self, request: Message) -> Message:
        pass

    @abstractmethod
    async def prepare_result_notification(self, request: Message) -> Message:
        pass
