from typing import Sequence

from spade.agent import Agent
from spade.message import Message

from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.utils.performative import Performative

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'


class InitiatorAgent(Agent):
    class InitiatorBehavior(RequestInitiator):
        def prepare_requests(self) -> Sequence[Message]:
            msg = Message(to=f'receiver@{XMPP_SERVER}')
            msg.set_metadata("performative", str(Performative.REQUEST))
            msg.body = "Request"
            return [msg]

        def handle_inform(self, response: Message):
            print(response.body)

    async def setup(self):
        print(f'Hello, I\'m {self.name}')
        self.add_behaviour(self.InitiatorBehavior())


class ResponderAgent(Agent):
    class ResponderBehaviour(RequestResponder):
        def prepare_result_notification(self, request: Message) -> Message:
            response: Message = request.make_reply()
            response.set_metadata("performative", str(Performative.INFORM.value))
            response.body = "Result"
            return response

    async def setup(self):
        print(f'Hello, I\'m {self.name}')
        self.add_behaviour(self.ResponderBehaviour())


if __name__ == "__main__":
    responder_agent = ResponderAgent(f'receiver@{XMPP_SERVER}', 'responder_password')
    future = responder_agent.start()
    future.result()
    initiator_agent = InitiatorAgent(f'initiator@{XMPP_SERVER}', 'initiator_password')
    initiator_agent.start()
