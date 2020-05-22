from abc import ABC
from typing import Dict, Type

from dataclasses import dataclass


@dataclass
class ContentElement:
    __key__ = 'content_element'


class Ontology(ABC):
    def __init__(self, name: str):
        self._concepts: Dict[str, Type[ContentElement]] = {}
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    def __getitem__(self, key: str):
        return self._concepts.get(key)

    def add(self, concept: Type[ContentElement]):
        if self._concepts.get(concept.__key__) is None:
            self._concepts[concept.__key__] = concept
        else:
            raise Exception('concept already exists in ontology')
