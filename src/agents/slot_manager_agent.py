from asyncio import Lock
from datetime import datetime
from typing import List, NamedTuple

from spade.template import Template

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_responder import ContractNetResponder
from src.behaviours.request_responder import RequestResponder
from src.ontology.port_terminal_ontology import AllocationProposal, \
    PortTerminalOntology, AllocationProposalAcceptance, AllocationConfirmation, DeallocationRequest, \
    AllocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class SlotItem(NamedTuple):
    container_id: str
    departure_time: datetime


class AllocationResponder(ContractNetResponder):

    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        if self.agent.is_full:
            return request.create_reply(Performative.REFUSE)
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, AllocationRequest):
            if self.agent.has_container(content.container_data.id):
                return request.create_reply(Performative.REFUSE)
            try:
                td: float = self.agent.get_timedelta_from_forced_reallocation_to_departure(
                    content.container_data.departure_time)
                response: ACLMessage = request.create_reply(Performative.PROPOSE)
                allocation_proposal = AllocationProposal(self.agent.slot_id, int(td))
                self.agent.content_manager.fill_content(allocation_proposal, response)
                return response
            except ValueError:
                pass
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        if self.agent.is_full:
            return request.create_reply(Performative.FAILURE)
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, AllocationProposalAcceptance):
            try:
                self.agent.add_container(content.container_data.id, content.container_data.departure_time)
                response = request.create_reply(Performative.INFORM)
                self.agent.content_manager.fill_content(AllocationConfirmation(self.agent.slot_id), response)
                return response
            except ValueError:
                pass
        return request.create_reply(Performative.NOT_UNDERSTOOD)


class DeallocationResponder(RequestResponder):

    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, DeallocationRequest):
            if self.agent.has_container(content.container_id):
                return request.create_reply(Performative.AGREE)
            else:
                return request.create_reply(Performative.REFUSE)
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        content: DeallocationRequest = self.agent.content_manager.extract_content(request)
        self.agent.remove_container(content.container_id)
        response = ACLMessage(
            to=str(request.sender),
            sender=str(self.agent.jid)
        )
        response.performative = Performative.INFORM
        response.action = DeallocationRequest.__key__
        return response


class SlotManagerAgent(BaseAgent):
    def __init__(self, jid: str, password: str, slot_id: str, max_height: int):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._slot_id: str = slot_id
        self._max_height: int = max_height
        self._containers: List[SlotItem] = []

    async def setup(self):
        allocation_mt = Template()
        allocation_mt.set_metadata('protocol', 'ContractNet')
        allocation_mt.set_metadata('action', AllocationRequest.__key__)

        deallocation_mt = Template()
        deallocation_mt.set_metadata('protocol', 'Request')
        deallocation_mt.set_metadata('action', DeallocationRequest.__key__)

        self._lock = Lock()
        self.add_behaviour(AllocationResponder(), allocation_mt)
        self.add_behaviour(DeallocationResponder(), deallocation_mt)
        self.log(f'Slot manager agent for slot no {self.slot_id} started')

    @property
    def slot_id(self) -> str:
        return self._slot_id

    @property
    def is_full(self):
        return len(self._containers) >= self._max_height

    def get_timedelta_from_forced_reallocation_to_departure(self, departure_time: str) -> float:
        if len(self._containers) == 0:
            return 0
        parsed_departure_time = datetime.fromisoformat(departure_time)
        return max(
            max([(parsed_departure_time - departure_time) for _, departure_time in self._containers]).total_seconds(),
            0
        )

    def add_container(self, container_id: str, departure_time: str):
        parsed_departure_time = datetime.fromisoformat(departure_time)
        self._containers.append(SlotItem(container_id, parsed_departure_time))

    def has_container(self, search_id: str) -> bool:
        return search_id in [container_id for container_id, _ in self._containers]

    def remove_container(self, container_id: str):
        self._containers = [slot_item for slot_item in self._containers if slot_item.container_id != container_id]
