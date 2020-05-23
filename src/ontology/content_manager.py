from dataclasses import asdict
from typing import Dict, Optional

from xmltodict import parse, unparse

from src.ontology.ontology import Ontology, ContentElement
from src.utils.acl_message import ACLMessage


class ContentManager:
    def __init__(self):
        self._ontologies: Dict[str, Ontology] = {}

    def register_ontology(self, ontology: Ontology):
        self._ontologies[ontology.name] = ontology

    def fill_content(self, content: ContentElement, msg: ACLMessage):
        msg.language = 'xml'
        msg.body = unparse({content.__key__: asdict(content)}, pretty=True)

    def extract_content(self, msg: ACLMessage) -> object:
        def postprocessor(path: str, key: str, value: str):
            try:
                return key, int(value)
            except (ValueError, TypeError):
                return key, value

        ontology: Optional[Ontology] = self._extract_ontology(msg)
        if ontology is None:
            raise Exception('Ontology is undefined')
        content_dict: Dict = parse(msg.body, dict_constructor=dict, postprocessor=postprocessor)
        element_key: str = list(content_dict.keys())[0]
        return ontology[element_key](**content_dict[element_key])

    def _extract_ontology(self, msg: ACLMessage) -> Optional[Ontology]:
        if msg.ontology is None:
            return None
        return self._ontologies.get(msg.ontology)
