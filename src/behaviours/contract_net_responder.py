from abc import ABCMeta
from enum import IntEnum

from spade.message import Message

from src.behaviours.responder import Responder
from src.utils.message_utils import get_performative
from src.utils.performative import Performative


class ContractNetResponderState(IntEnum):
    WAITING_FOR_CFP = 0
    WAITING_FOR_PROPOSAL_RESPONSE = 1


class ContractNetResponder(Responder, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self._state = ContractNetResponderState.WAITING_FOR_CFP

    async def run(self):
        if self._state == ContractNetResponderState.WAITING_FOR_CFP:
            cfp: Message = await self.receive()
            if cfp is not None:
                response: Message = self.prepare_response(cfp)
                if get_performative(response) == Performative.PROPOSE:
                    self._state = ContractNetResponderState.WAITING_FOR_PROPOSAL_RESPONSE
                await self.send(response)
            return

        if self._state == ContractNetResponderState.WAITING_FOR_PROPOSAL_RESPONSE:
            proposal_response: Message = await self.receive()
            if proposal_response is not None:
                if get_performative(proposal_response) == Performative.ACCEPT_PROPOSAL:
                    result_notification: Message = await self.prepare_result_notification(proposal_response)
                    await self.send(result_notification)
                self._state = ContractNetResponderState.WAITING_FOR_CFP
            return
