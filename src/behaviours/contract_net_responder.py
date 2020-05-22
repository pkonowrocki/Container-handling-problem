from abc import ABCMeta
from enum import IntEnum

from src.behaviours.responder import Responder
from src.utils.acl_message import ACLMessage
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
            cfp: ACLMessage = await self.receive()
            if cfp is not None:
                response: ACLMessage = self.prepare_response(cfp)
                if response.performative == Performative.PROPOSE:
                    self._state = ContractNetResponderState.WAITING_FOR_PROPOSAL_RESPONSE
                await self.send(response)
            return

        if self._state == ContractNetResponderState.WAITING_FOR_PROPOSAL_RESPONSE:
            proposal_response: ACLMessage = await self.receive()
            if proposal_response is not None:
                if proposal_response.performative == Performative.ACCEPT_PROPOSAL:
                    result_notification: ACLMessage = await self.prepare_result_notification(proposal_response)
                    await self.send(result_notification)
                self._state = ContractNetResponderState.WAITING_FOR_CFP
            return
