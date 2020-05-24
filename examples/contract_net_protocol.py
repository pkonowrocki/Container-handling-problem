import asyncio
import random
from typing import Sequence, List

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_initiator import ContractNetInitiator
from src.behaviours.contract_net_responder import ContractNetResponder
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'
RESPONDERS_COUNT = 4


class InitiatorAgent(BaseAgent):
    class InitiatorBehavior(ContractNetInitiator):
        async def prepare_cfps(self) -> Sequence[ACLMessage]:
            return [self._prepare_cfp(f'responder{k}@{XMPP_SERVER}') for k in range(RESPONDERS_COUNT)]

        def handle_inform(self, response: ACLMessage):
            print(f'{self.agent.name}: INFORM received from {response.sender}')

        def handle_refuse(self, response: ACLMessage):
            print(f'{self.agent.name}: REFUSE received from {response.sender}')

        def handle_all_responses(self, responses: Sequence[ACLMessage], acceptances: List[ACLMessage],
                                 rejections: List[ACLMessage]):
            proposals: Sequence[ACLMessage] = [msg for msg in responses if msg.performative == Performative.PROPOSE]
            min_price: int = min(int(msg.body) for msg in proposals)
            best_proposals: Sequence[ACLMessage] = [msg for msg in proposals if int(msg.body) == min_price]
            selected_proposal: ACLMessage = random.choice(best_proposals)
            acceptances.append(selected_proposal.create_reply(Performative.ACCEPT_PROPOSAL))
            for msg in proposals:
                if msg.id != selected_proposal.id:
                    rejections.append(msg.create_reply(Performative.REJECT_PROPOSAL))

        def _prepare_cfp(self, receiver: str) -> ACLMessage:
            msg = ACLMessage(to=receiver)
            msg.performative = Performative.CFP
            return msg

    async def setup(self):
        print(f'{self.name}: Hello, I\'m {self.name}')
        self.add_behaviour(self.InitiatorBehavior())


class ResponderAgent(BaseAgent):
    class ResponderBehaviour(ContractNetResponder):
        async def prepare_response(self, request: ACLMessage) -> ACLMessage:
            print(f'{self.agent.name}: REQUEST received from {request.sender}')
            msg = request.create_reply(Performative.PROPOSE)
            msg.body = str(random.randint(1, 10))
            return msg

        async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
            print(f'{self.agent.name}: ACCEPT-PROPOSAL received from {request.sender}')
            await asyncio.sleep(random.randint(1, 4))
            return request.create_reply(Performative.INFORM)

    async def setup(self):
        print(f'{self.name}: Hello, I\'m {self.name}')
        self.add_behaviour(self.ResponderBehaviour())


if __name__ == "__main__":
    for i in range(RESPONDERS_COUNT):
        responder_agent = ResponderAgent(f'responder{i}@{XMPP_SERVER}', 'responder_password')
        future = responder_agent.start()
        future.result()
    initiator_agent = InitiatorAgent(f'initiator@{XMPP_SERVER}', 'initiator_password')
    initiator_agent.start()
