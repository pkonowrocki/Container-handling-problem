from datetime import datetime
from typing import Sequence

from spade.behaviour import TimeoutBehaviour

from src.agents.base_agent import BaseAgent
from src.ontology.port_terminal_ontology import PortTerminalOntology


class ForceContainersDeallocation(TimeoutBehaviour):
    async def run(self):
        self.agent.log('Forcing containers reallocation')

    def on_end(self):
        self.agent.kill()


class TruckAgent(BaseAgent):
    def __init__(self, jid: str, password: str, containers_jids: Sequence[str], arrival_time: datetime):
        super().__init__(jid, password, PortTerminalOntology.instance())
        self._containers_jids = containers_jids
        self._arrival_time = arrival_time

    def setup(self):
        self.add_behaviour(ForceContainersDeallocation(self._arrival_time))

    @property
    def containers_jids(self) -> Sequence[str]:
        return self._containers_jids
