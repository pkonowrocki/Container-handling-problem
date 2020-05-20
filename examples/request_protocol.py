import asyncio
import random
from typing import Sequence

from spade.agent import Agent
from spade.message import Message

from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.utils.performative import Performative

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'
RESPONDERS_COUNT = 4


class InitiatorAgent(Agent):
    class InitiatorBehavior(RequestInitiator):
        def prepare_requests(self) -> Sequence[Message]:
            return [self._prepare_request(f'responder{i}@{XMPP_SERVER}') for i in range(RESPONDERS_COUNT)]

        def handle_inform(self, response: Message):
            print(f'{self.agent.name}: INFORM received from {response.sender}')

        def handle_agree(self, response: Message):
            print(f'{self.agent.name}: AGREE received from {response.sender}')

        def _prepare_request(self, receiver: str) -> Message:
            msg = Message(to=receiver)
            msg.set_metadata("performative", str(Performative.REQUEST.value))
            return msg

    async def setup(self):
        print(f'{self.name}: Hello, I\'m {self.name}')
        self.add_behaviour(self.InitiatorBehavior())


class ResponderAgent(Agent):
    class ResponderBehaviour(RequestResponder):
        def prepare_response(self, request: Message) -> Message:
            print(f'{self.agent.name}: REQUEST received from {request.sender}')
            msg = request.make_reply()
            msg.set_metadata("performative", str(Performative.AGREE.value))
            return msg

        async def prepare_result_notification(self, request: Message) -> Message:
            await asyncio.sleep(random.randint(1, 4))
            response: Message = Message(to=str(request.sender))
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
