from enum import IntEnum
from typing import Optional

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from src.utils.performative import Performative


class RequestResponderState(IntEnum):
    INITIALISED = 0,
    REQUEST_RECEIVED = 1,
    AGREED = 2,
    FINALIZED = 3


class RequestResponder(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self._state = RequestResponderState.INITIALISED
        self._request: Optional[Message] = None

    async def run(self):
        if self._state == RequestResponderState.INITIALISED:
            request: Message = await self.receive()
            if request is not None:
                self._state = RequestResponderState.REQUEST_RECEIVED
            return
        if self._state == RequestResponderState.REQUEST_RECEIVED:
            response: Message = self.prepare_response(self._request)
            if response is not None:
                await self.send(response)
                if response.metadata.performative == Performative.AGREE:
                    self._state = RequestResponderState.AGREED
                else:
                    self._state = RequestResponderState.FINALIZED
            return
        if self._state == RequestResponderState.AGREED:
            response: Message = self.prepare_result_notification(self._request)
            await self.send(response)
            self._state = RequestResponderState.FINALIZED
            return
        if self._state == RequestResponderState.FINALIZED:
            self._state = RequestResponderState.INITIALISED

    def prepare_response(self, request: Message) -> Optional[Message]:
        return None

    def prepare_result_notification(self, request: Message) -> Message:
        return request.make_reply()
