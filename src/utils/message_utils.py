from aioxmpp import JID
from spade.message import Message

from src.utils.performative import Performative

def get_action(msg: Message) -> str:
    return msg.get_metadata("action")

def get_performative(msg: Message) -> Performative:
    return Performative(int(msg.get_metadata("performative")))

def set_performative(msg: Message, performative: Performative) -> Message:
    msg.set_metadata("performative", performative.value)
    return msg

def get_language(msg: Message) -> str:
    return msg.get_metadata("language")

def get_ontology(msg: Message) -> str:
    return msg.get_metadata("ontology")

def jid_to_str(jid: JID) -> str:
    return f'{jid.localpart}@{jid.domain}{f"{jid.resource}" if jid.resource is not None else ""}'
