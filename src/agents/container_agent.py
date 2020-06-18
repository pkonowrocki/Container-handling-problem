import math
from asyncio import Lock
from datetime import datetime
from typing import Sequence, List

from spade.behaviour import TimeoutBehaviour
from spade.template import Template

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_initiator import ContractNetInitiator
from src.behaviours.request_initiator import RequestInitiator
from src.behaviours.request_responder import RequestResponder
from src.ontology.ontology import ContentElement
from src.ontology.port_terminal_ontology import PortTerminalOntology, ContainerData, AllocationProposal, \
    AllocationConfirmation, AllocationProposalAcceptance, DeallocationRequest, AllocationRequest, ReallocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class AllocationInitiator(ContractNetInitiator):
    def __init__(self, slot_manager_agents_jids: Sequence[str], is_first_allocation: bool = True):
        super().__init__()
        self._slot_manager_agents_jids = slot_manager_agents_jids
        self._is_first_allocation = is_first_allocation

    async def prepare_cfps(self) -> Sequence[ACLMessage]:
        if self._is_first_allocation:
            await self.agent.acquire_lock()
        cfps = [self._create_cfp(jid) for jid in self._slot_manager_agents_jids]
        return cfps

    def handle_all_responses(self, responses: Sequence[ACLMessage], acceptances: List[ACLMessage],
                             rejections: List[ACLMessage]):
        proposals = [msg for msg in responses if msg.performative == Performative.PROPOSE]
        self._create_proposals_replies(proposals, acceptances, rejections)

    def handle_inform(self, response: ACLMessage):
        content: ContentElement = self.agent.content_manager.extract_content(response)
        if isinstance(content, AllocationConfirmation):
            self.agent.log(f'Container successfully allocated in slot no {content.slot_id}')
            self.agent.slot_id = content.slot_id
            self.agent.slot_jid = str(response.sender)
            if self._is_first_allocation:
                self.agent.release_lock()
        else:
            self.agent.log('Allocation failed')
            self.agent.kill()

    def handle_failure(self, response: ACLMessage):
        self.agent.log('Allocation failed')
        self.agent.kill()

    def _create_cfp(self, jid: str):
        cfp: ACLMessage = ACLMessage(
            to=jid,
            sender=str(self.agent.jid)
        )
        cfp.performative = Performative.CFP
        cfp.ontology = self.agent.ontology.name
        cfp.protocol = 'ContractNet'
        cfp.action = AllocationRequest.__key__
        container_data: ContentElement = ContainerData(str(self.agent.jid), self.agent.departure_time)
        content: ContentElement = AllocationRequest(container_data)
        self.agent.content_manager.fill_content(content, cfp)
        return cfp

    def _create_proposals_replies(self, proposals: Sequence[ACLMessage], acceptances: List[ACLMessage],
                                  rejections: List[ACLMessage]):
        def fetch_allocation_eval(proposal: ACLMessage) -> float:
            content: ContentElement = self.agent.content_manager.extract_content(proposal)
            if isinstance(content, AllocationProposal):
                return content.seconds_from_forced_reallocation_to_departure
            return math.inf

        best_proposal: ACLMessage = min(proposals, key=fetch_allocation_eval)
        acceptance = best_proposal.create_reply(Performative.ACCEPT_PROPOSAL)
        acceptance_content: ContentElement = AllocationProposalAcceptance(
            ContainerData(self.agent.jid, str(self.agent.departure_time)))
        self.agent.content_manager.fill_content(acceptance_content, acceptance)
        acceptances.append(acceptance)
        for msg in proposals:
            if msg.id != best_proposal.id:
                rejections.append(msg.create_reply(Performative.REJECT_PROPOSAL))


class DeallocationInitiator(RequestInitiator):

    async def prepare_requests(self) -> Sequence[ACLMessage]:
        await self.agent.acquire_lock()
        if self.agent.slot_jid is None:
            raise Exception('Container is not allocated')
        request = ACLMessage(
            to=self.agent.slot_jid,
            sender=str(self.agent.jid)
        )
        request.protocol = 'Request'
        request.ontology = self.agent.ontology.name
        self.agent.content_manager.fill_content(DeallocationRequest(self.agent.jid), request)
        return [request]

    def handle_refuse(self, response: ACLMessage):
        self.agent.log('Deallocation refused')
        self.agent.release_lock()

    def handle_inform(self, response: ACLMessage):
        self.agent.slot_id = None
        self.agent.slot_jid = None
        self.agent.log(f'Deallocation succeeded. Delay: {str(datetime.now() - self.agent.departure_time)}')
        self.agent.release_lock()

    def handle_failure(self, response: ACLMessage):
        self.agent.log('Deallocation failed')
        self.agent.release_lock()


class DeallocationLauncher(TimeoutBehaviour):
    async def run(self):
        deallocation_initiator = DeallocationInitiator()
        self.agent.add_behaviour(deallocation_initiator)
        await deallocation_initiator.join()
        await self.agent.stop()


class ReallocationResponder(RequestResponder):
    async def prepare_response(self, request: ACLMessage) -> ACLMessage:
        content: ContentElement = self.agent.content_manager.extract_content(request)
        if isinstance(content, ReallocationRequest):
            await self.agent.acquire_lock()
            return request.create_reply(Performative.AGREE)
        return request.create_reply(Performative.NOT_UNDERSTOOD)

    async def prepare_result_notification(self, request: ACLMessage) -> ACLMessage:
        allocation_mt = Template()
        allocation_mt.set_metadata('protocol', 'ContractNet')
        allocation_mt.set_metadata('action', AllocationRequest.__key__)
        allocation_behaviour = AllocationInitiator(self.agent.available_slots_jids, False)

        self.agent.add_behaviour(allocation_behaviour, allocation_mt)
        await allocation_behaviour.join()

        response = ACLMessage(
            to=str(request.sender),
            sender=str(self.agent.jid)
        )
        response.performative = Performative.INFORM
        response.action = ReallocationRequest.__key__
        self.agent.release_lock()
        return response


class ContainerAgent(BaseAgent):
    def __init__(self, jid: str, password: str, slot_manager_agents_jids: Sequence[str], departure_time: datetime):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._slot_manager_agents_jids = slot_manager_agents_jids  # TODO: Replace this line with fetching jids from DF
        self._departure_time: datetime = departure_time
        self._slot_id = None
        self._slot_jid = None

    async def setup(self):
        allocation_mt = Template()
        allocation_mt.set_metadata('protocol', 'ContractNet')
        allocation_mt.set_metadata('action', AllocationRequest.__key__)

        deallocation_mt = Template()
        deallocation_mt.set_metadata('protocol', 'ContractNet')
        deallocation_mt.set_metadata('action', DeallocationRequest.__key__)

        reallocation_mt = Template()
        reallocation_mt.set_metadata('protocol', 'Request')
        reallocation_mt.set_metadata('action', ReallocationRequest.__key__)

        self._lock = Lock()
        self.add_behaviour(AllocationInitiator(self.available_slots_jids), allocation_mt)
        self.add_behaviour(DeallocationLauncher(self.departure_time), deallocation_mt)
        self.add_behaviour(ReallocationResponder(), reallocation_mt)
        self.log(f'Container agent for {self.name} started.')

    @property
    def departure_time(self) -> datetime:
        return self._departure_time

    @property
    def slot_id(self) -> str:
        return self._slot_id

    @slot_id.setter
    def slot_id(self, value: str):
        self._slot_id = value

    @property
    def slot_jid(self) -> str:
        return self._slot_jid

    @slot_jid.setter
    def slot_jid(self, value: str):
        self._slot_jid = value

    @property
    def available_slots_jids(self):
        return [jid for jid in self._slot_manager_agents_jids if jid != self.slot_jid]
