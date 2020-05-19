import asyncio
from typing import Sequence

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
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
            print(f'INFORM received from {response.sender}')

        def handle_agree(self, response: Message):
            print(f'AGREE received from {response.sender}')

        def _prepare_request(self, receiver: str) -> Message:
            msg = Message(to=receiver)
            msg.set_metadata("performative", str(Performative.REQUEST))
            msg.body = "Request"
            return  msg

    async def setup(self):
        print(f'Hello, I\'m {self.name}')
        self.add_behaviour(self.InitiatorBehavior())


class ResponderAgent(Agent):
    def __init__(self, jid, password, sleep_time):
        super().__init__(jid, password)
        self.sleep_time = sleep_time

    class ResponderBehaviour(RequestResponder):
        async def prepare_response(self, request: Message) -> Message:
            print(f'REQUEST received from {request.sender}')
            await asyncio.sleep(self.agent.sleep_time)
            msg = request.make_reply()
            msg.set_metadata("performative", str(Performative.AGREE.value))
            return msg

        async def prepare_result_notification(self, request: Message) -> Message:
            await asyncio.sleep(self.agent.sleep_time)
            response: Message = request.make_reply()
            response.set_metadata("performative", str(Performative.INFORM.value))
            response.body = "Result"
            return response

    async def setup(self):
        print(f'Hello, I\'m {self.name}')
        self.add_behaviour(self.ResponderBehaviour())


if __name__ == "__main__":
    for i in range(RESPONDERS_COUNT):
        responder_agent = ResponderAgent(f'responder{i}@{XMPP_SERVER}', 'responder_password', i)
        future = responder_agent.start()
        future.result()
    initiator_agent = InitiatorAgent(f'initiator@{XMPP_SERVER}', 'initiator_password')
    initiator_agent.start()
