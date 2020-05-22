from typing import Sequence

from spade.agent import Agent

from src.ontology.content_manager import ContentManager
from src.ontology.ontology import Ontology


class BaseAgent(Agent):
    def __init__(self, jid: str, password: str, ontologies: Sequence[Ontology] = ()):
        super().__init__(jid, password)
        self._content_manager = ContentManager()
        for onto in ontologies:
            self._content_manager.register_ontology(onto)

    @property
    def content_manager(self) -> ContentManager:
        return self._content_manager

    def log(self, text: str):
        print(f'{self.name}: {text}')
