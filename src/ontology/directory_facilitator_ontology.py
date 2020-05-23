from dataclasses import dataclass
from typing import Dict, Sequence

from src.ontology.ontology import ContentElement, Ontology
from src.utils.nested_dataclass import nested_dataclass


@dataclass
class ServiceDescription(ContentElement):
    properties: Dict[str, object]


@nested_dataclass
class DFAgentDescription(ContentElement):
    agentName: str
    interactionProtocol: str
    ontology: str
    language: str
    service: ServiceDescription


@nested_dataclass
class DFAgentDescriptionList(ContentElement):
    list: Sequence[DFAgentDescription]


class RegisterServiceOntology(Ontology):
    def __init__(self):
        super().__init__('RegisterServiceOntology')
        self.add(DFAgentDescription)


class SearchServiceRequestOntology(Ontology):
    def __init__(self):
        super().__init__('SearchServiceRequestOntology')
        self.add(DFAgentDescription)


class SearchServiceResponseOntology(Ontology):
    def __init__(self):
        super().__init__('SearchServiceResponseOntology')
        self.add(DFAgentDescriptionList)


class DeleteServiceOntology(Ontology):
    def __init__(self):
        super().__init__('DeleteServiceOntology')
        self.add(DFAgentDescription)

