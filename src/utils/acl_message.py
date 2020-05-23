from spade.message import Message

from src.utils.performative import Performative


class ACLMessage(Message):
    PERFORMATIVE_KEY = 'performative'
    ONTOLOGY_KEY = 'ontology'
    LANGUAGE_KEY = 'language'
    ACTION_KEY = 'action'

    @property
    def performative(self) -> Performative:
        return Performative(int(self.get_metadata(self.PERFORMATIVE_KEY)))

    @performative.setter
    def performative(self, value: Performative):
        self.set_metadata(self.PERFORMATIVE_KEY, str(value.value))

    @property
    def ontology(self) -> str:
        return self.get_metadata(self.ONTOLOGY_KEY)

    @ontology.setter
    def ontology(self, value: str):
        self.set_metadata(self.ONTOLOGY_KEY, value)

    @property
    def language(self) -> str:
        return self.get_metadata(self.LANGUAGE_KEY)

    @language.setter
    def language(self, value: str):
        self.set_metadata(self.LANGUAGE_KEY, value)

    @property
    def action(self) -> str:
        return self.get_metadata(self.ACTION_KEY)

    @action.setter
    def action(self, value: str):
        self.set_metadata(self.ACTION_KEY, value)

    def create_reply(self, performative: Performative) -> 'ACLMessage':
        reply = self.make_reply()
        reply.__class__ = ACLMessage
        reply.performative = performative
        reply.body = None
        return reply
