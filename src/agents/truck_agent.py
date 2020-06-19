from datetime import datetime
from typing import Sequence

from spade.behaviour import TimeoutBehaviour

from src.agents.base_agent import BaseAgent
from src.behaviours.request_initiator import RequestInitiator
from src.ontology.port_terminal_ontology import PortTerminalOntology, ContainersDeallocationRequest
from src.utils.acl_message import ACLMessage
from src.utils.performative import Performative


class ContainersDeallocationInititiator(RequestInitiator):
    async def prepare_requests(self) -> Sequence[ACLMessage]:
        request = ACLMessage(to=self.agent.port_manager_agent_jid)
        request.protocol = 'Request'
        request.ontology = self.agent.ontology.name
        self.agent.content_manager.fill_content(ContainersDeallocationRequest(self.agent.containers_jids), request)
        return [request]

    def handle_all_result_notifications(self, result_notifications: Sequence[ACLMessage]):
        success_count = len([msg for msg in result_notifications if msg.performative == Performative.INFORM])
        self.agent.log(f'{success_count}/{len(self.agent.containers_jids)} containers successfully deallocated')


class ContainersDeallocationLauncher(TimeoutBehaviour):
    async def run(self):
        deallocate_containers_behaviour = ContainersDeallocationInititiator()
        self.agent.add_behaviour(deallocate_containers_behaviour)
        await deallocate_containers_behaviour.join()

    def on_end(self):
        self.agent.kill()


class TruckAgent(BaseAgent):
    def __init__(self, jid: str, password: str,
                 containers_jids: Sequence[str], arrival_time: datetime, port_manager_agent_jid: str):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._containers_jids = containers_jids
        self._arrival_time = arrival_time
        self._port_manager_agent_jid = port_manager_agent_jid

    def setup(self):
        self.add_behaviour(ContainersDeallocationLauncher(self._arrival_time))

    @property
    def containers_jids(self) -> Sequence[str]:
        return self._containers_jids

    @property
    def port_manager_agent_jid(self):
        return self._port_manager_agent_jid
