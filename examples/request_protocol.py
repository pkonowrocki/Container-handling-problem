import asyncio
import random
from typing import Sequence

from src.agents.base_agent import BaseAgent
from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'
RESPONDERS_COUNT = 4


class InitiatorAgent(BaseAgent):
    class InitiatorBehavior(RequestInitiator):
        def prepare_requests(self) -> Sequence[ACLMessage]:
            return [self._prepare_request(f'responder{k}@{XMPP_SERVER}') for k in range(RESPONDERS_COUNT)]

        def handle_inform(self, response: ACLMessage):
            print(f'{self.agent.name}: INFORM received from {response.sender}')

        def handle_agree(self, response: ACLMessage):
            print(f'{self.agent.name}: AGREE received from {response.sender}')

        def _prepare_request(self, receiver: str) -> ACLMessage:
            msg = ACLMessage(to=receiver)
            msg.performative = Performative.REQUEST
            return msg

    async def setup(self):
        print(f'{self.name}: Hello, I\'m {self.name}')
        self.add_behaviour(self.InitiatorBehavior())


class ResponderAgent(BaseAgent):
    class ResponderBehaviour(RequestResponder):
        def prepare_response(self, request: ACLMessage) -> ACLMessage:
            print(f'{self.agent.name}: REQUEST received from {request.sender}')
            return request.create_reply(Performative.AGREE)

        async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
            await asyncio.sleep(random.randint(1, 4))
            response: ACLMessage = ACLMessage(to=str(request.sender))
            response.performative = Performative.INFORM
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
