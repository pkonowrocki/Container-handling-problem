from asyncio import Lock
from datetime import datetime
from typing import List, NamedTuple, Sequence

from spade.template import Template

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_responder import ContractNetResponder
from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.ontology.port_terminal_ontology import AllocationProposal, \
    PortTerminalOntology, AllocationProposalAcceptance, AllocationConfirmation, DeallocationRequest, \
    AllocationRequest, ReallocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class SlotItem(NamedTuple):
    container_id: str
    departure_time: datetime
    container_agent_jid: str


class AllocationResponder(ContractNetResponder):

    async def handle_cfp(self, cfp: ACLMessage) -> ACLMessage:
        await self.agent.acquire_lock()
        if self.agent.is_full:
            self.agent.release_lock()
            return cfp.create_reply(Performative.REFUSE)
        content = self.agent.content_manager.extract_content(cfp)
        if isinstance(content, AllocationRequest):
            if self.agent.has_container(content.container_data.id):
                self.agent.release_lock()
                return cfp.create_reply(Performative.REFUSE)
            try:
                td: float = self.agent.get_timedelta_from_forced_reallocation_to_departure(
                    content.container_data.departure_time)
                response: ACLMessage = cfp.create_reply(Performative.PROPOSE)
                allocation_proposal = AllocationProposal(self.agent.slot_id, int(td))
                self.agent.content_manager.fill_content(allocation_proposal, response)
                self.agent.release_lock()
                return response
            except ValueError:
                pass
        self.agent.release_lock()
        return cfp.create_reply(Performative.NOT_UNDERSTOOD)

    async def handle_accept_proposal(self, accept: ACLMessage) -> ACLMessage:
        await self.agent.acquire_lock()
        if self.agent.is_full:
            self.agent.release_lock()
            return accept.create_reply(Performative.FAILURE)
        content = self.agent.content_manager.extract_content(accept)
        if isinstance(content, AllocationProposalAcceptance):
            try:
                self.agent.add_container(
                    content.container_data.id,
                    content.container_data.departure_time,
                    str(accept.sender)
                )
                self.agent.release_lock()
                response = accept.create_reply(Performative.INFORM)
                self.agent.content_manager.fill_content(AllocationConfirmation(self.agent.slot_id), response)
                return response
            except ValueError:
                pass
        self.agent.release_lock()
        return accept.create_reply(Performative.NOT_UNDERSTOOD)

    async def handle_reject_proposal(self, reject: ACLMessage):
        pass


class DeallocationResponder(RequestResponder):

    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, DeallocationRequest):
            await self.agent.acquire_lock()
            if self.agent.has_container(content.container_id):
                return request.create_reply(Performative.AGREE)
            else:
                self.agent.release_lock()
                return request.create_reply(Performative.REFUSE)
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        content: DeallocationRequest = self.agent.content_manager.extract_content(request)
        blocking_containers = self.agent.get_blocking_containers(content.container_id)
        for container_id, _, container_agent_jid in blocking_containers:
            self.agent.remove_container(container_id)
            await self._reallocate_container(container_agent_jid)
        self.agent.remove_container(content.container_id)
        self.agent.release_lock()
        response = ACLMessage(
            to=str(request.sender),
            sender=str(self.agent.jid)
        )
        request.protocol = 'Request'
        request.ontology = self.agent.ontology.name
        response.performative = Performative.INFORM
        response.action = DeallocationRequest.__key__
        return response

    async def _reallocate_container(self, container_jid: str):
        reallocate_behaviour = ReallocationInitiator(container_jid)
        reallocation_mt = Template()
        reallocation_mt.set_metadata('protocol', 'Request')
        reallocation_mt.set_metadata('action', ReallocationRequest.__key__)

        self.agent.add_behaviour(reallocate_behaviour, reallocation_mt)
        await reallocate_behaviour.join()


class ReallocationInitiator(RequestInitiator):
    def __init__(self, container_jid: str):
        super().__init__()
        self._container_jid = container_jid

    async def prepare_requests(self) -> Sequence[ACLMessage]:
        request = ACLMessage(
            to=self._container_jid,
            sender=str(self.agent.jid)
        )
        request.protocol = 'Request'
        request.ontology = self.agent.ontology.name
        self.agent.content_manager.fill_content(ReallocationRequest(self.agent.slot_id), request)
        return [request]

    def handle_refuse(self, response: ACLMessage):
        raise Exception('Container cannot refuse reallocation')

    def handle_failure(self, response: ACLMessage):
        raise Exception('Reallocation error occurred')


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
            max(
                [(parsed_departure_time - departure_time) for _, departure_time, _ in self._containers]
            ).total_seconds(),
            0
        )

    def add_container(self, container_id: str, departure_time: str, container_agent_jid: str):
        parsed_departure_time = datetime.fromisoformat(departure_time)
        self._containers.append(SlotItem(container_id, parsed_departure_time, container_agent_jid))

    def has_container(self, search_id: str) -> bool:
        return search_id in [container_id for container_id, _, _ in self._containers]

    def remove_container(self, container_id: str):
        self._containers = [slot_item for slot_item in self._containers if slot_item.container_id != container_id]

    def get_blocking_containers(self, container_id) -> Sequence[SlotItem]:
        blocking_containers: List[SlotItem] = []
        for i in range(len(self._containers)):
            cur_container = self._containers[-i - 1]
            if cur_container.container_id == container_id:
                break
            blocking_containers.append(cur_container)
        return blocking_containers
