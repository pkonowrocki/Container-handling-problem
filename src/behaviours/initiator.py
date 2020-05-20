from abc import ABCMeta

from spade.behaviour import CyclicBehaviour
from spade.message import Message

from src.utils.message_utils import get_performative
from src.utils.performative import Performative


class Initiator(CyclicBehaviour, metaclass=ABCMeta):
    def _handle_single_message(self, msg: Message) -> None:
        performative: Performative = get_performative(msg)
        {
            Performative.AGREE: self.handle_agree,
            Performative.PROPOSE: self.handle_propose,
            Performative.REFUSE: self.handle_refuse,
            Performative.NOT_UNDERSTOOD: self.handle_not_understood,
            Performative.INFORM: self.handle_inform,
            Performative.FAILURE: self.handle_failure
        }[performative](msg)

    def handle_agree(self, response: Message):
        pass

    def handle_propose(self, response: Message):
        pass

    def handle_refuse(self, response: Message):
        pass

    def handle_not_understood(self, response: Message):
        pass

    def handle_inform(self, response: Message):
        pass

    def handle_failure(self, response: Message):
        pass
