import multiprocessing
import random
import signal
from datetime import datetime, timedelta, time
from dataclasses import dataclass
from typing import List, Sequence

from aioxmpp import JID

from src.agents.container_agent import ContainerAgent, SlotJid
from src.agents.slot_manager_agent import SlotManagerAgent


@dataclass
class ContainerData:
    jid: str
    arrival_time: datetime
    departure_time: datetime


@dataclass
class TruckData:
    id: int
    departure_time: datetime
    container_jids: Sequence[str]


class TestEnvironment:
    def __init__(self, domain: str, max_slot_height: int, slot_count: int, container_count):
        self._domain = domain
        self._max_slot_height = max_slot_height
        self._slot_count = slot_count
        self._container_count = container_count
        self._container_move_count = 0

    def prepare_test(self, max_contaneirs_in_batch):
        containers = []
        arrival_time = datetime.now() + timedelta(seconds=5)
        containers_left = self._container_count
        while containers_left > 0:
            arrival_time += timedelta(seconds=random.randint(0, 10))
            if containers_left > max_contaneirs_in_batch:
                containers_batch = random.randint(1, max_contaneirs_in_batch)
            else:
                containers_batch = random.randint(1, containers_left)

            for i in range(containers_batch):
                container_id = self._container_count - containers_left + i
                departure_time = arrival_time + timedelta(seconds=random.randint(20, 40))
                new_container = ContainerData(f'container_{container_id}@{self._domain}', arrival_time, departure_time)
                containers.append(new_container)
            containers_left -= containers_batch

        return containers
