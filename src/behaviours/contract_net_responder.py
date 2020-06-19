from abc import ABCMeta, abstractmethod
from enum import IntEnum

from src.behaviours.base_cyclic_behaviour import BaseCyclicBehaviour
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class ContractNetResponderState(IntEnum):
    WAITING_FOR_CFP = 0
    WAITING_FOR_PROPOSAL_RESPONSE = 1


class ContractNetResponder(BaseCyclicBehaviour, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self._state = ContractNetResponderState.WAITING_FOR_CFP

    async def run(self):
        if self._state == ContractNetResponderState.WAITING_FOR_CFP:
            cfp: ACLMessage = await self.receive()
            if cfp is not None:
                response: ACLMessage = await self.handle_cfp(cfp)
                if response.performative == Performative.PROPOSE:
                    self._state = ContractNetResponderState.WAITING_FOR_PROPOSAL_RESPONSE
                await self.send(response)
            return

        if self._state == ContractNetResponderState.WAITING_FOR_PROPOSAL_RESPONSE:
            proposal_response: ACLMessage = await self.receive()
            if proposal_response is not None:
                if proposal_response.performative == Performative.ACCEPT_PROPOSAL:
                    result_notification: ACLMessage = await self.handle_accept_proposal(proposal_response)
                    await self.send(result_notification)
                elif proposal_response.performative == Performative.REJECT_PROPOSAL:
                    await self.handle_reject_proposal(proposal_response)
                self._state = ContractNetResponderState.WAITING_FOR_CFP
            return

    @abstractmethod
    async def handle_cfp(self, cfp: ACLMessage) -> ACLMessage:
        pass

    @abstractmethod
    async def handle_accept_proposal(self, accept: ACLMessage) -> ACLMessage:
        pass

    @abstractmethod
    async def handle_reject_proposal(self, reject: ACLMessage):
        pass
