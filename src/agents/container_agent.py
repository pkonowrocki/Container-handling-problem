from asyncio import Lock
from typing import Sequence, List

from spade.message import Message

from src.agents.base_agent import BaseAgent
from src.behaviours.contract_net_initiator import ContractNetInitiator
from src.ontology.ontology import ContentElement
from src.ontology.port_terminal_ontology import PortTerminalOntology, ContainerData


class ContainerAgent(BaseAgent):
    class AllocationInitiator(ContractNetInitiator):

        def prepare_cfps(self) -> Sequence[Message]:
            self.agent.acquire_lock()
            return [self._create_cfp(jid) for jid in self.agent.slot_manager_agents_jids]

        def handle_all_responses(self, responses: Sequence[Message], acceptances: List[Message],
                                 rejections: List[Message]):
            pass

        def _create_cfp(self, jid: str):
            cfp: Message = Message(
                to=jid,
                sender=self.agent.name
            )
            cfp.set_metadata('ontology', self.agent.ontology.name)
            content: ContentElement = ContainerData(self.agent.jid, self.agent.departure_time)
            self.agent.content_manager.fill_content(content, cfp)
            return cfp

    def __init__(self, jid: str, password: str, slot_manager_agents_jids: Sequence[str], departure_time: str):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._lock = Lock()
        self._slot_manager_agents_jids = slot_manager_agents_jids  # TODO: Replace this line with fetching jids from DF
        self._departure_time = departure_time

    @property
    def slot_manager_agents_jids(self) -> Sequence[str]:
        return self._slot_manager_agents_jids

    @property
    def departure_time(self):
        return self._departure_time

    def acquire_lock(self):
        self._lock.acquire()

    def release_lock(self):
        self._lock.release()
