import asyncio
from abc import abstractmethod
from enum import IntEnum
from typing import Sequence

from spade.message import Message

from src.behaviours.initiator import Initiator
from src.utils.message_utils import get_performative
from src.utils.performative import Performative


class RequestInitiatorState(IntEnum):
    INITIALISED = 0,
    WAITING_FOR_RESPONSES = 1,
    ALL_RESULT_NOTIFICATIONS_RECEIVED = 2,
    FINALIZED = 3


class RequestInitiator(Initiator):
    def __init__(self):
        super().__init__()
        self._requests_count: int = 0
        self._responses_count: int = 0
        self._result_notifications_count: int = 0
        self._expected_result_notifications_count: int = 0
        self._state: RequestInitiatorState = RequestInitiatorState.INITIALISED
        self._responses = []
        self._result_notifications = []

    async def run(self):
        if self._state == RequestInitiatorState.INITIALISED:
            requests: Sequence[Message] = self.prepare_requests()
            self._requests_count = len(requests)
            self._expected_result_notifications_count = len(requests)
            await asyncio.wait([self.send(msg) for msg in requests])
            self._state = RequestInitiatorState.WAITING_FOR_RESPONSES
            return

        if self._state == RequestInitiatorState.WAITING_FOR_RESPONSES:
            response: Message = await self.receive()
            if response is not None:
                print(response)
                performative: Performative = get_performative(response)
                if performative in [Performative.INFORM, Performative.FAILURE]:
                    self._result_notifications.append(response)
                    self._result_notifications_count += 1
                elif performative in [Performative.AGREE, Performative.NOT_UNDERSTOOD, Performative.REFUSE]:
                    self._responses.append(response)
                    self._responses_count += 1
                    if performative != Performative.AGREE:
                        self._expected_result_notifications_count -= 1
                    if self._responses_count >= self._requests_count:
                        self.handle_all_responses(self._responses)
                if self._result_notifications_count >= self._expected_result_notifications_count:
                    self._state = RequestInitiatorState.ALL_RESULT_NOTIFICATIONS_RECEIVED
                self._handle_single_message(response)
            return

        if self._state == RequestInitiatorState.ALL_RESULT_NOTIFICATIONS_RECEIVED:
            self.handle_all_responses(self._result_notifications)
            self._state = RequestInitiatorState.FINALIZED
            return

    def _done(self) -> bool:
        return self._state == RequestInitiatorState.FINALIZED

    @abstractmethod
    def prepare_requests(self) -> Sequence[Message]:
        pass

    def handle_all_responses(self, responses: Sequence[Message]):
        pass

    def handle_all_result_notifications(self, result_notifications: Sequence[Message]):
        pass
