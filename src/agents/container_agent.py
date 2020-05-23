import math
from typing import Sequence, List

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_initiator import ContractNetInitiator
from src.ontology.ontology import ContentElement
from src.ontology.port_terminal_ontology import PortTerminalOntology, ContainerData, AllocationProposal, \
    AllocationConfirmation, AllocationProposalAcceptance
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class AllocationInitiator(ContractNetInitiator):
    async def prepare_cfps(self) -> Sequence[ACLMessage]:
        return [self._create_cfp(jid) for jid in self.agent.slot_manager_agents_jids]

    def handle_all_responses(self, responses: Sequence[ACLMessage], acceptances: List[ACLMessage],
                             rejections: List[ACLMessage]):
        proposals = [msg for msg in responses if msg.performative == Performative.PROPOSE]
        self._create_proposals_replies(proposals, acceptances, rejections)

    def handle_inform(self, response: ACLMessage):
        content: ContentElement = self.agent.content_manager.extract_content(response)
        if isinstance(content, AllocationConfirmation):
            self.agent.log(f'Container successfully allocated in slot no {content.slot_id}')
            self.agent.slot_id = content.slot_id
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
        content: ContentElement = ContainerData(self.agent.jid, self.agent.departure_time)
        self.agent.content_manager.fill_content(content, cfp)
        return cfp

    def _create_proposals_replies(self, proposals: Sequence[ACLMessage], acceptances: List[ACLMessage],
                                  rejections: List[ACLMessage]):
        def fetch_allocation_eval(msg: ACLMessage) -> float:
            content: ContentElement = self.agent.content_manager.extract_content(msg)
            if isinstance(content, AllocationProposal):
                return content.seconds_from_forced_reallocation_to_departure
            return math.inf

        best_proposal: ACLMessage = min(proposals, key=fetch_allocation_eval)
        acceptance = best_proposal.create_reply(Performative.ACCEPT_PROPOSAL)
        acceptance_content: ContentElement = AllocationProposalAcceptance(
            ContainerData(self.agent.jid, self.agent.departure_time))
        self.agent.content_manager.fill_content(acceptance_content, acceptance)
        acceptances.append(acceptance)
        for msg in proposals:
            if msg.id != best_proposal.id:
                rejections.append(msg.create_reply(Performative.REJECT_PROPOSAL))


class ContainerAgent(BaseAgent):
    def __init__(self, jid: str, password: str, slot_manager_agents_jids: Sequence[str], departure_time: str):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._slot_manager_agents_jids = slot_manager_agents_jids  # TODO: Replace this line with fetching jids from DF
        self._departure_time = departure_time
        self._slot_id = None

    async def setup(self):
        self.add_behaviour(AllocationInitiator())

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
