import asyncio
from abc import abstractmethod
from enum import IntEnum
from typing import Sequence, List

from spade.message import Message

from src.behaviours.initiator import Initiator


class ContractNetInitiatorState(IntEnum):
    PREPARE_CFPS = 0
    WAITING_FOR_RESPONSES = 1
    ALL_RESPONSES_RECEIVED = 2
    WAITING_FOR_RESULT_NOTIFICATIONS = 3
    ALL_RESULT_NOTIFICATIONS_RECEIVED = 4
    FINALIZED = 5


class ContractNetInitiator(Initiator):
    def __init__(self):
        super().__init__()
        self._state = ContractNetInitiatorState.PREPARE_CFPS
        self._cfps_count = 0
        self._responses_count = 0
        self._responses = []
        self._expected_result_notifications_count = 0
        self._result_notifications_count = 0
        self._result_notifications = []

    async def run(self):
        if self._state == ContractNetInitiatorState.PREPARE_CFPS:
            cfps: Sequence[Message] = self.prepare_cfps()
            self._cfps_count = len(cfps)
            await asyncio.wait([self.send(msg) for msg in cfps])
            self._state = ContractNetInitiatorState.WAITING_FOR_RESPONSES
            return
        if self._state == ContractNetInitiatorState.WAITING_FOR_RESPONSES:
            response: Message = await self.receive()
            if response is not None:
                self._handle_single_message(response)
                self._responses.append(response)
                self._responses_count += 1
            if self._responses_count >= self._cfps_count:
                self._state = ContractNetInitiatorState.ALL_RESPONSES_RECEIVED
            return
        if self._state == ContractNetInitiatorState.ALL_RESPONSES_RECEIVED:
            acceptances: List[Message] = []
            self.handle_all_responses(self._responses, acceptances)
            self._expected_result_notifications_count = len(acceptances)
            await asyncio.wait([self.send(msg) for msg in acceptances])
            self._state = ContractNetInitiatorState.WAITING_FOR_RESULT_NOTIFICATIONS
            return
        if self._state == ContractNetInitiatorState.WAITING_FOR_RESULT_NOTIFICATIONS:
            result_notification: Message = await self.receive()
            if result_notification is not None:
                self._handle_single_message(result_notification)
                self._result_notifications.append(result_notification)
                self._result_notifications_count += 0
            if self._result_notifications_count >= self._expected_result_notifications_count:
                self._state = ContractNetInitiatorState.ALL_RESULT_NOTIFICATIONS_RECEIVED
            return
        if self._state == ContractNetInitiatorState.ALL_RESULT_NOTIFICATIONS_RECEIVED:
            self.handle_all_result_notifications(self._result_notifications)
            self._state = ContractNetInitiatorState.FINALIZED

    def _done(self) -> bool:
        return self._state == ContractNetInitiatorState.FINALIZED

    @abstractmethod
    def prepare_cfps(self) -> Sequence[Message]:
        pass

    @abstractmethod
    def handle_all_responses(self, responses: Sequence[Message], acceptances: List[Message]):
        pass

    def handle_all_result_notifications(self, result_notifications: Sequence[Message]):
        pass
