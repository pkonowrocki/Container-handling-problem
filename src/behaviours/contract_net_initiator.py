import asyncio
from abc import abstractmethod
from enum import IntEnum
from typing import Sequence, List

from src.behaviours.initiator import Initiator
from src.utils.acl_message import ACLMessage


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
            cfps: Sequence[ACLMessage] = await self.prepare_cfps()
            self._cfps_count = len(cfps)
            await asyncio.wait([self.send(msg) for msg in cfps])
            self._state = ContractNetInitiatorState.WAITING_FOR_RESPONSES
            return

        if self._state == ContractNetInitiatorState.WAITING_FOR_RESPONSES:
            response: ACLMessage = await self.receive()
            if response is not None:
                self._handle_single_message(response)
                self._responses.append(response)
                self._responses_count += 1
            if self._responses_count >= self._cfps_count:
                self._state = ContractNetInitiatorState.ALL_RESPONSES_RECEIVED
            return

        if self._state == ContractNetInitiatorState.ALL_RESPONSES_RECEIVED:
            acceptances: List[ACLMessage] = []
            rejections: List[ACLMessage] = []
            self.handle_all_responses(self._responses, acceptances, rejections)
            self._expected_result_notifications_count = len(acceptances)
            await asyncio.wait([self.send(msg) for msg in acceptances + rejections])
            self._state = ContractNetInitiatorState.WAITING_FOR_RESULT_NOTIFICATIONS
            return

        if self._state == ContractNetInitiatorState.WAITING_FOR_RESULT_NOTIFICATIONS:
            result_notification: ACLMessage = await self.receive()
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
            return

    def _done(self) -> bool:
        return self._state == ContractNetInitiatorState.FINALIZED

    @abstractmethod
    async def prepare_cfps(self) -> Sequence[ACLMessage]:
        pass

    @abstractmethod
    def handle_all_responses(self, responses: Sequence[ACLMessage], acceptances: List[ACLMessage],
                             rejections: List[ACLMessage]):
        pass

    def handle_all_result_notifications(self, result_notifications: Sequence[ACLMessage]):
        pass
