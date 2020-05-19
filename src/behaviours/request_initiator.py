import asyncio
from abc import abstractmethod
from enum import IntEnum
from typing import Sequence

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from src.utils.performative import Performative


class RequestInitiatorState(IntEnum):
    INITIALISED = 0,
    WAITING_FOR_RESPONSES = 1,
    ALL_RESPONSES_RECEIVED = 2,
    FINALIZED = 3


class RequestInitiator(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self._requests_count: int = 0
        self._responses_count: int = 0
        self._state: RequestInitiatorState = RequestInitiatorState.INITIALISED
        self._responses = []

    async def run(self):
        if self._state == RequestInitiatorState.INITIALISED:
            requests: Sequence[Message] = self.prepare_requests()
            self._requests_count = len(requests)
            await asyncio.wait([self.send(msg) for msg in requests])
            self._state = RequestInitiatorState.WAITING_FOR_RESPONSES
            return

        if self._state == RequestInitiatorState.WAITING_FOR_RESPONSES:
            response: Message = await self.receive()
            if response is not None:
                self._responses.append(response)
                self._responses_count += 1
                self._handle_single_message(response)
                if self._responses_count >= self._requests_count:
                    self._state = RequestInitiatorState.ALL_RESPONSES_RECEIVED
            return

        if self._state == RequestInitiatorState.ALL_RESPONSES_RECEIVED:
            self.handle_all_responses(self._responses)
            self._state = RequestInitiatorState.FINALIZED
            return

    def _done(self) -> bool:
        return self._state == RequestInitiatorState.FINALIZED

    def _handle_single_message(self, msg: Message) -> None:
        performative: Performative = Performative(int(msg.get_metadata("performative")))
        {
            Performative.AGREE: self.handle_agree,
            Performative.REFUSE: self.handle_refuse,
            Performative.NOT_UNDERSTOOD: self.handle_not_understood,
            Performative.INFORM: self.handle_inform,
            Performative.FAILURE: self.handle_failure
        }[performative](msg)

    @abstractmethod
    def prepare_requests(self) -> Sequence[Message]:
        pass

    def handle_all_responses(self, responses: Sequence[Message]):
        pass

    def handle_agree(self, response: Message):
        pass

    def handle_refuse(self, response: Message):
        pass

    def handle_inform(self, response: Message):
        pass

    def handle_not_understood(self, response: Message):
        pass

    def handle_failure(self, response: Message):
        pass
