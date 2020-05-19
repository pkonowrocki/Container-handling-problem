from spade.message import Message

from src.utils.performative import Performative


def get_performative(msg: Message) -> Performative:
    return Performative(int(msg.get_metadata("performative")))
