from typing import Dict, Optional

from dataclasses import asdict
from spade.message import Message
from xmltodict import parse, unparse

from src.ontology.ontology import Ontology, ContentElement


class ContentManager:
    def __init__(self):
        self._ontologies: Dict[str, Ontology] = {}

    def register_ontology(self, ontology: Ontology):
        self._ontologies[ontology.name] = ontology

    def fill_content(self, content: ContentElement, msg: Message):
        msg.set_metadata('language', 'xml')
        msg.body = unparse({content.__key__: asdict(content)}, pretty=True)

    def extract_content(self, msg: Message) -> object:
        ontology: Optional[Ontology] = self._extract_ontology(msg)
        if ontology is None:
            raise Exception('Ontology is undefined')
        content_dict: Dict = parse(msg.body, dict_constructor=dict)
        key: str = list(content_dict.keys())[0]
        return ontology[key](**content_dict[key])

    def _extract_ontology(self, msg: Message) -> Optional[Ontology]:
        ontology_name = msg.get_metadata('ontology')
        if ontology_name is None:
            return None
        return self._ontologies.get(ontology_name)
