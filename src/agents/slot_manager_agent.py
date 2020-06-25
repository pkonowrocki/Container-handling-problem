from asyncio import Lock
from datetime import datetime
from typing import List, NamedTuple, Sequence

import aiohttp
from aiohttp import web
from spade.template import Template

from src.agents.DFAgent import DFService, HandleRegisterRequestBehaviour
from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_responder import ContractNetResponder
from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.ontology.directory_facilitator_ontology import DFAgentDescription, ServiceDescription
from src.ontology.port_terminal_ontology import AllocationProposal, \
    PortTerminalOntology, AllocationProposalAcceptance, AllocationConfirmation, SelfDeallocationRequest, \
    AllocationRequest, ReallocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.content_language import ContentLanguage
from src.utils.interaction_protocol import InteractionProtocol
from src.utils.jid_utils import jid_to_str
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
                await self.agent.add_container(
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


class SelfDeallocationResponder(RequestResponder):

    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        content = self.agent.content_manager.extract_content(request)
        if isinstance(content, SelfDeallocationRequest):
            await self.agent.acquire_lock()
            if self.agent.has_container(content.container_id):
                return request.create_reply(Performative.AGREE)
            else:
                self.agent.release_lock()
                return request.create_reply(Performative.REFUSE)
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        content: SelfDeallocationRequest = self.agent.content_manager.extract_content(request)
        blocking_containers = self.agent.get_blocking_containers(content.container_id)
        for container_id, _, container_agent_jid in blocking_containers:
            await self.agent.remove_container(container_id)
            await self._reallocate_container(container_agent_jid)
        await self.agent.remove_container(content.container_id)
        self.agent.release_lock()
        response = ACLMessage(
            to=str(request.sender),
            sender=str(self.agent.jid)
        )
        response.protocol = 'Request'
        response.ontology = self.agent.ontology.name
        response.performative = Performative.INFORM
        response.action = SelfDeallocationRequest.__key__
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
        request = ACLMessage(to=self._container_jid)
        request.performative = Performative.REQUEST
        request.protocol = 'Request'
        request.ontology = self.agent.ontology.name
        self.agent.content_manager.fill_content(ReallocationRequest(self.agent.slot_id), request)
        return [request]

    def handle_refuse(self, response: ACLMessage):
        raise Exception('Container cannot refuse reallocation')

    def handle_failure(self, response: ACLMessage):
        raise Exception('Reallocation error occurred')


class HandleRegistrationBehaviour(HandleRegisterRequestBehaviour):
    def __init__(self):
        super(HandleRegistrationBehaviour, self).__init__()

    async def handleFailure(self, result: ACLMessage):
        self.agent.log('Registration problem')
        raise Exception('Registration problem')

    async def handleAccept(self, result: ACLMessage):
        self.agent.log('Registered')


class SlotManagerAgent(BaseAgent):
    def __init__(self, jid: str, password: str, slot_id: str, max_height: int):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._slot_id: str = slot_id
        self._max_height: int = max_height
        self._containers: List[SlotItem] = []
        self._ws = web.WebSocketResponse()
        self._prepared = False

    async def setup(self):
        self.web.add_get("/slot", self.slot_controller, "slot.html")
        self.web.add_get("/ws", self.ws_controller, template=None, raw=True)
        self.web.start(port=8000 + int(self._slot_id), templates_path="../src/templates")
        allocation_mt = Template()
        allocation_mt.set_metadata('protocol', 'ContractNet')
        allocation_mt.set_metadata('action', AllocationRequest.__key__)

        self_deallocation_mt = Template()
        self_deallocation_mt.set_metadata('protocol', 'Request')
        self_deallocation_mt.set_metadata('action', SelfDeallocationRequest.__key__)
        await self.register_service()
        self._lock = Lock()
        self.add_behaviour(AllocationResponder(), allocation_mt)
        self.add_behaviour(SelfDeallocationResponder(), self_deallocation_mt)
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

    async def add_container(self, container_id: str, departure_time: str, container_agent_jid: str):
        parsed_departure_time = datetime.fromisoformat(departure_time)
        self._containers.append(SlotItem(container_id, parsed_departure_time, container_agent_jid))
        if self._prepared:
            await self._ws.send_json({"containers": self.containers})

    def has_container(self, search_id: str) -> bool:
        return search_id in [container_id for container_id, _, _ in self._containers]

    async def remove_container(self, container_id: str):
        self._containers = [slot_item for slot_item in self._containers if slot_item.container_id != container_id]
        if self._prepared:
            await self._ws.send_json({"containers": self.containers})

    def get_blocking_containers(self, container_id) -> Sequence[SlotItem]:
        blocking_containers: List[SlotItem] = []
        for i in range(len(self._containers)):
            cur_container = self._containers[-i - 1]
            if cur_container.container_id == container_id:
                break
            blocking_containers.append(cur_container)
        return blocking_containers

    @property
    def containers(self):
        return [container_id for container_id, _, _ in self._containers]

    async def slot_controller(self, request):
        return {"containers": self.containers, "containerHeight": int(100 / self._max_height)}

    async def ws_controller(self, request):
        await self._ws.prepare(request)
        self._prepared = True

        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await self._ws.close()
                else:
                    await self._ws.send_str(msg.data + '/answer')
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      self._ws.exception())

        print('websocket connection closed')

        return self._ws

    async def register_service(self):
        self.log('start registration')
        serviceDescription: ServiceDescription = ServiceDescription({
            'slot_id': self._slot_id
        })
        dfd: DFAgentDescription = DFAgentDescription(jid_to_str(self.jid), '', 'port_terminal_ontology',
                                                     ContentLanguage.XML, serviceDescription)
        await DFService.register(self, dfd, HandleRegistrationBehaviour())
