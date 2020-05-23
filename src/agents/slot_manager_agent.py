from asyncio import Lock
from datetime import datetime, timedelta
from typing import List, NamedTuple

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_responder import ContractNetResponder
from src.ontology.port_terminal_ontology import ContainerData, AllocationProposal, AllocationConfirmation
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class SlotItem(NamedTuple):
    container_id: str
    departure_time: datetime


class AllocationResponder(ContractNetResponder):

    def prepare_response(self, request: ACLMessage) -> ACLMessage:
        if self.agent.is_full:
            return request.create_reply(Performative.REFUSE)
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, ContainerData):
            try:
                self.agent.acquire_lock()
                td: timedelta = self.agent.get_timedelta_from_forced_reallocation_to_departure(content.departure_time)
                response: ACLMessage = request.create_reply(Performative.PROPOSE)
                allocation_proposal = AllocationProposal(self.agent.slot_id, int(td.total_seconds()))
                self.agent.content_manager.fill_content(allocation_proposal, response)
                return response
            except ValueError:
                self.agent.release_lock()
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        if self.agent.is_full:
            self.agent.release_lock()
            return request.create_reply(Performative.FAILURE)
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, AllocationConfirmation):
            try:
                self.agent.add_container(content.container_data.id, content.container_data.departure_time)
                self.agent.release_lock()
                return request.create_reply(Performative.INFORM)
            except ValueError:
                pass
        self.agent.release_lock()
        return request.create_reply(Performative.NOT_UNDERSTOOD)


class SlotManagerAgent(BaseAgent):
    def __init__(self, jid: str, password: str, slot_id: str, max_height: int):
        super().__init__(jid, password)
        self._slot_id: str = slot_id
        self._max_height: int = max_height
        self._containers: List[SlotItem] = []
        self._lock = Lock()

    def setup(self):
        pass

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
        return max(max([(parsed_departure_time - departure_time) for _, departure_time in self._containers]), 0)

    def add_container(self, container_id: str, departure_time: str):
        parsed_departure_time = datetime.fromisoformat(departure_time)
        self._containers.append(SlotItem(container_id, parsed_departure_time))

    def acquire_lock(self):
        self._lock.acquire()

    def release_lock(self):
        self._lock.release()
