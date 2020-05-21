import asyncio
import random
from typing import Sequence, List

from spade.agent import Agent
from spade.message import Message

from src.behaviours.contract_net_initiator import ContractNetInitiator
from src.behaviours.contract_net_responder import ContractNetResponder
from src.utils.message_utils import get_performative
from src.utils.performative import Performative

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'
RESPONDERS_COUNT = 4


class InitiatorAgent(Agent):
    class InitiatorBehavior(ContractNetInitiator):
        def prepare_cfps(self) -> Sequence[Message]:
            return [self._prepare_cfp(f'responder{k}@{XMPP_SERVER}') for k in range(RESPONDERS_COUNT)]

        def handle_inform(self, response: Message):
            print(f'{self.agent.name}: INFORM received from {response.sender}')

        def handle_refuse(self, response: Message):
            print(f'{self.agent.name}: REFUSE received from {response.sender}')

        def handle_all_responses(self, responses: Sequence[Message], acceptances: List[Message], rejections: List[Message]):
            proposals: Sequence[Message] = [msg for msg in responses if get_performative(msg) == Performative.PROPOSE]
            min_price: int = min(int(msg.body) for msg in proposals)
            best_proposals: Sequence[Message] = [msg for msg in proposals if int(msg.body) == min_price]
            selected_proposal: Message = random.choice(best_proposals)
            acceptance: Message = selected_proposal.make_reply()
            acceptance.set_metadata('performative', str(Performative.ACCEPT_PROPOSAL.value))
            acceptances.append(acceptance)
            for msg in proposals:
                if msg.id != selected_proposal.id:
                    rejections.append(self._create_rejection(msg))

        def _prepare_cfp(self, receiver: str) -> Message:
            msg = Message(to=receiver)
            msg.set_metadata("performative", str(Performative.CFP.value))
            return msg

        def _create_rejection(self, msg: Message):
            rejection = msg.make_reply()
            rejection.set_metadata('performative', str(Performative.REJECT_PROPOSAL.value))
            return rejection

    async def setup(self):
        print(f'{self.name}: Hello, I\'m {self.name}')
        self.add_behaviour(self.InitiatorBehavior())


class ResponderAgent(Agent):
    class ResponderBehaviour(ContractNetResponder):
        def prepare_response(self, request: Message) -> Message:
            print(f'{self.agent.name}: REQUEST received from {request.sender}')
            msg = request.make_reply()
            msg.set_metadata("performative", str(Performative.PROPOSE.value))
            msg.body = str(random.randint(1, 10))
            return msg

        async def prepare_result_notification(self, request: Message) -> Message:
            print(f'{self.agent.name}: ACCEPT-PROPOSAL received from {request.sender}')
            await asyncio.sleep(random.randint(1, 4))
            response: Message = request.make_reply()
            response.set_metadata("performative", str(Performative.INFORM.value))
            return response

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
