from dataclasses import dataclass

from src.ontology.ontology import Ontology, ContentElement, Action
from src.utils.nested_dataclass import nested_dataclass
from src.utils.singleton import Singleton


@dataclass
class ContainerData(ContentElement):
    id: str
    departure_time: str
    __key__ = 'container_data'


@nested_dataclass
class AllocationRequest(Action):
    container_data: ContainerData
    __key__ = 'allocation_request'


@dataclass
class AllocationProposal(ContentElement):
    slot_id: str
    seconds_from_forced_reallocation_to_departure: int
    __key__ = 'allocation_proposal'


@dataclass
class AllocationConfirmation(ContentElement):
    slot_id: str
    __key__ = 'allocation_confirmation'


@nested_dataclass
class AllocationProposalAcceptance(ContentElement):
    container_data: ContainerData
    __key__ = 'allocation_proposal_acceptance'


@dataclass
class DeallocationRequest(Action):
    container_id: str
    __key__ = 'deallocation_request'


@Singleton
class PortTerminalOntology(Ontology):
    def __init__(self):
        super().__init__('port_terminal_ontology')
        # TODO: Add more content elements when needed
        self.add(ContainerData)
        self.add(AllocationRequest)
        self.add(AllocationProposal)
        self.add(AllocationConfirmation)
        self.add(AllocationProposalAcceptance)
        self.add(DeallocationRequest)
