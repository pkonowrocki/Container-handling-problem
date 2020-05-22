import math
from asyncio import Lock
from typing import Sequence, List

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_initiator import ContractNetInitiator
from src.ontology.ontology import ContentElement
from src.ontology.port_terminal_ontology import PortTerminalOntology, ContainerData, AllocationProposal, \
    AllocationConfirmation
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class AllocationInitiator(ContractNetInitiator):
    def prepare_cfps(self) -> Sequence[ACLMessage]:
        self.agent.acquire_lock()
        return [self._create_cfp(jid) for jid in self.agent.slot_manager_agents_jids]

    def handle_all_responses(self, responses: Sequence[ACLMessage], acceptances: List[ACLMessage],
                             rejections: List[ACLMessage]):
        proposals = [msg for msg in responses if msg.performative == Performative.PROPOSE]
        self._create_proposals_replies(proposals, acceptances, rejections)

    def handle_inform(self, response: ACLMessage):
        content: ContentElement = self.agent.content_manager.extract_content(response)
        if isinstance(content, AllocationConfirmation):
            self.agent.slot_id = content.slot_id
            self.agent.release_lock()
        else:
            self.agent.log('Allocation failed')
            self.agent.release_lock()
            self.agent.kill()

    def handle_failure(self, response: ACLMessage):
        self.agent.log('Allocation failed')
        self.agent.release_lock()
        self.agent.kill()

    def _create_cfp(self, jid: str):
        cfp: ACLMessage = ACLMessage(
            to=jid,
            sender=self.agent.name
        )
        cfp.performative = Performative.CFP
        cfp.ontology = self.agent.ontology.name
        content: ContentElement = ContainerData(self.agent.jid, self.agent.departure_time)
        self.agent.content_manager.fill_content(content, cfp)
        return cfp

    def _create_proposals_replies(self, proposals: Sequence[ACLMessage], acceptances: List[ACLMessage],
                                  rejections: List[ACLMessage]):
        def fetch_time_to_forced_reallocation(msg: ACLMessage) -> float:
            content: ContentElement = self.agent.content_manager.extract_content(msg)
            if isinstance(content, AllocationProposal):
                return content.time_to_forced_reallocation
            return math.inf

        best_proposal: ACLMessage = max(proposals, key=fetch_time_to_forced_reallocation)
        acceptances.append(best_proposal.create_reply(Performative.ACCEPT_PROPOSAL))
        for msg in proposals:
            if msg.id != best_proposal.id:
                rejections.append(msg.create_reply(Performative.REJECT_PROPOSAL))


class ContainerAgent(BaseAgent):
    def __init__(self, jid: str, password: str, slot_manager_agents_jids: Sequence[str], departure_time: str):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._lock = Lock()
        self._slot_manager_agents_jids = slot_manager_agents_jids  # TODO: Replace this line with fetching jids from DF
        self._departure_time = departure_time
        self._slot_id = None

    @property
    def slot_manager_agents_jids(self) -> Sequence[str]:
        return self._slot_manager_agents_jids

    @property
    def departure_time(self) -> str:
        return self._departure_time

    @property
    def slot_id(self) -> str:
        return self._slot_id

    @slot_id.setter
    def slot_id(self, value: str):
        self._slot_id = value

    def acquire_lock(self):
        self._lock.acquire()

    def release_lock(self):
        self._lock.release()
