from dataclasses import dataclass

from src.ontology.ontology import Ontology, ContentElement


@dataclass
class ContainerData(ContentElement):
    id: str
    departure_time: str
    __key__ = 'container_data'


@dataclass
class AllocationProposal(ContentElement):
    slot_id: str
    time_to_forced_reallocation: int
    __key__ = 'allocation_proposal'


class PortTerminalOntology(Ontology):
    def __init__(self):
        super().__init__('port_terminal_ontology')
        # TODO: Add more content elements when needed
        self.add(ContainerData)
        self.add(AllocationProposal)
