from typing import Dict, Sequence

from src.ontology.ontology import ContentElement, Ontology, Action
from src.utils.nested_dataclass import nested_dataclass
from src.utils.singleton import Singleton


@nested_dataclass
class ServiceDescription(ContentElement):
    properties: Dict[str, str]
    __key__ = 'service-description'


@nested_dataclass
class DFAgentDescription(ContentElement):
    agentName: str
    interactionProtocol: str
    ontology: str
    language: str
    service: ServiceDescription
    __key__ = 'df-agent-description'


@nested_dataclass
class SearchServiceRequest(Action):
    request: DFAgentDescription
    __key__ = 'search-service-request'


@nested_dataclass
class SearchServiceResponse(Action):
    list: Sequence[DFAgentDescription]
    __key__ = 'search-service-response'


@nested_dataclass
class RegisterService(Action):
    request: DFAgentDescription
    __key__ = 'register-service-request'


@nested_dataclass
class DeregisterService(Action):
    request: DFAgentDescription
    __key__ = 'deregister-service-request'


@Singleton
class DFOntology(Ontology):
    def __init__(self):
        super().__init__('DFOntology')
        self.add(DFAgentDescription)
        self.add(ServiceDescription)
        self.add(RegisterService)
        self.add(DeregisterService)
        self.add(SearchServiceResponse)
        self.add(SearchServiceRequest)
