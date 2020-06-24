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


def _sort_by_arrival(container: ContainerData):
    return container.arrival_time


def _sort_by_departure(container: ContainerData):
    return container.departure_time


class TestEnvironment:
    def __init__(self, domain: str, max_slot_height: int, slot_count: int, container_count):
        self._domain = domain
        self._max_slot_height = max_slot_height
        self._slot_count = slot_count
        self._container_count = container_count
        self._container_move_count = 0

    def prepare_test(self, max_containers_in_batch):
        containers = []
        arrival_time = datetime.now() + timedelta(seconds=5)
        containers_left = self._container_count
        while containers_left > 0:
            arrival_time += timedelta(seconds=random.randint(3, 3))
            if containers_left > max_containers_in_batch:
                containers_batch = random.randint(1, max_containers_in_batch)
            else:
                containers_batch = random.randint(1, containers_left)

            for i in range(containers_batch):
                container_id = self._container_count - containers_left + i
                departure_time = arrival_time + timedelta(seconds=random.randint(10, 10))
                new_container = ContainerData(f'container_{container_id}@{self._domain}', arrival_time, departure_time)
                containers.append(new_container)
            containers_left -= containers_batch

        return containers

    def get_moves_count_for_naive_method(self, containers_data: List[ContainerData]):
        slots: List[List[ContainerData]] = [[] for i in range(self._slot_count)]

        arriving_containers = containers_data.copy()
        departing_containers = containers_data.copy()
        arriving_containers.sort(key=_sort_by_arrival)
        departing_containers.sort(key=_sort_by_departure)
        moves = 0
        while len(arriving_containers) > 0 or len(departing_containers) > 0:
            if not len(arriving_containers) == 0 and \
                    (arriving_containers[0].arrival_time < departing_containers[0].departure_time):
                arriving_container = arriving_containers.pop(0)
                self._allocate_container(slots, arriving_container)
                moves += 1
            else:
                departing_container = departing_containers.pop(0)
                slot_id = 0
                found = False
                while not found:
                    try:
                        container_index = slots[slot_id].index(departing_container)
                        found = True
                    except ValueError:
                        slot_id += 1
                top_container_index = len(slots[slot_id]) - 1
                while top_container_index > container_index:
                    container_to_move = slots[slot_id].pop()
                    self._allocate_container(slots, container_to_move, slot_id)
                    moves += 1
                    top_container_index -= 1
                slots[slot_id].pop()
                moves += 1

        return moves

    def _allocate_container(self, slots, container, not_to_slot=-1):
        new_slot_id = 0
        while len(slots[new_slot_id]) >= self._max_slot_height or new_slot_id == not_to_slot:
            new_slot_id += 1
        slots[new_slot_id].append(container)
