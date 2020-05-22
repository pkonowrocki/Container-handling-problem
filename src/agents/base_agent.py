from spade.agent import Agent

from src.ontology.content_manager import ContentManager
from src.ontology.ontology import Ontology


class BaseAgent(Agent):
    def __init__(self, jid: str, password: str, ontology: Ontology = None):
        super().__init__(jid, password)
        self._content_manager = ContentManager()
        self._ontology = ontology
        if ontology is not None:
            self._content_manager.register_ontology(ontology)

    @property
    def content_manager(self) -> ContentManager:
        return self._content_manager

    @property
    def ontology(self):
        return self._ontology

    def log(self, text: str):
        print(f'{self.name}: {text}')
