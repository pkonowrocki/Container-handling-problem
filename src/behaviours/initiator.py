from abc import ABCMeta
from typing import Dict, Callable, Optional

from src.behaviours.base_cyclic_behaviour import BaseCyclicBehaviour
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class Initiator(BaseCyclicBehaviour, metaclass=ABCMeta):
    def _handle_single_message(self, msg: ACLMessage) -> None:
        handlers_dict: Dict[Performative, Callable[[ACLMessage], None]] = {
            Performative.AGREE: self.handle_agree,
            Performative.PROPOSE: self.handle_propose,
            Performative.REFUSE: self.handle_refuse,
            Performative.NOT_UNDERSTOOD: self.handle_not_understood,
            Performative.INFORM: self.handle_inform,
            Performative.FAILURE: self.handle_failure
        }
        handler: Optional[Callable[[ACLMessage], None]] = handlers_dict.get(msg.performative)
        if handler is not None:
            handler(msg)

    def handle_agree(self, response: ACLMessage):
        pass

    def handle_propose(self, response: ACLMessage):
        pass

    def handle_refuse(self, response: ACLMessage):
        pass

    def handle_not_understood(self, response: ACLMessage):
        pass

    def handle_inform(self, response: ACLMessage):
        pass

    def handle_failure(self, response: ACLMessage):
        pass
