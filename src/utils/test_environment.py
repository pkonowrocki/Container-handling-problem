import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import List, Sequence

from src.utils.singleton import Singleton


@dataclass
class ContainerData:
    jid: str
    arrival_time: datetime
    departure_time: datetime
    estimated_departure_time: datetime


@dataclass
class TruckData:
    id: int
    departure_time: datetime
    container_jids: Sequence[str]


def _sort_by_arrival(container: ContainerData):
    return container.arrival_time


def _sort_by_departure(container: ContainerData):
    return container.departure_time


@Singleton
class TestEnvironment:
    def __init__(self):
        self._domain = ""
        self._max_slot_height = 0
        self._slot_count = 0
        self._container_count = 0
        self._container_move_count = 0
        self._lock = Lock()

    def setup(self, domain: str, max_slot_height: int, slot_count: int, container_count):
        self._domain = domain
        self._max_slot_height = max_slot_height
        self._slot_count = slot_count
        self._container_count = container_count
        self._container_move_count = 0

    def prepare_test(self, max_containers_in_batch, min_arrival_delta, max_arrival_delta, min_departure_delta,
                     max_departure_delta, departure_time_accuracy):
        containers = []
        arrival_time = datetime.now() + timedelta(seconds=5)
        containers_left = self._container_count
        while containers_left > 0:
            arrival_time += timedelta(seconds=random.randint(min_arrival_delta, max_arrival_delta))
            if containers_left > max_containers_in_batch:
                containers_batch = random.randint(1, max_containers_in_batch)
            else:
                containers_batch = random.randint(1, containers_left)

            for i in range(containers_batch):
                container_id = self._container_count - containers_left + i
                departure_time = arrival_time + timedelta(seconds=random.randint(min_departure_delta,
                                                                                 max_departure_delta))
                estimated_departure_time = departure_time + timedelta(seconds=random.randint(-departure_time_accuracy,
                                                                                             departure_time_accuracy))
                new_container = ContainerData(f'container_{container_id}@{self._domain}',
                                              arrival_time,
                                              departure_time,
                                              estimated_departure_time)
                containers.append(new_container)
            containers_left -= containers_batch

        return containers

    def increment_moves_counter(self):
        self._lock.acquire()
        self._container_move_count += 1
        print(f"Current moves count: {self._container_move_count}")
        self._lock.release()

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
