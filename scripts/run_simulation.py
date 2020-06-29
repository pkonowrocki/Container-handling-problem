import asyncio
import signal
import sys
from datetime import datetime, timedelta
from time import sleep
from typing import Sequence

import click

from src.agents.DFAgent import DFService, DFAgent

from src.agents.port_manager_agent import PortManagerAgent
from src.agents.truck_agent import TruckAgent
from src.utils.test_environment import TestEnvironment

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent
from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = '192.168.0.24'


def run_slot_manager_agent(slot_id: str, domain: str, max_height: int):
    slot_manager_agent = SlotManagerAgent(f'slot_{slot_id}@{domain}', 'slot_password', slot_id, max_height)
    future = slot_manager_agent.start()
    future.result()
    return slot_manager_agent


def run_container_agent(container_jid: str, departure_time: datetime):
    container_agent = ContainerAgent(container_jid, 'container_password', departure_time)
    future = container_agent.start()
    future.result()
    return container_agent


def run_truck_agent(truck_id: int, domain: str, arrival_time: datetime, containers_jids: Sequence[str],
                    port_manager_agent_jid: str):
    truck_agent = TruckAgent(f'truck_{truck_id}@{domain}', 'truck_password', containers_jids, arrival_time,
                             port_manager_agent_jid)
    future = truck_agent.start()
    future.result()


def run_port_manager_agent(jid: str):
    port_manager_agent = PortManagerAgent(jid, 'port_manager_password')
    port_manager_agent.start()


def initializer():
    """Ignore SIGINT in child workers."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


@click.command()
@click.option('--domain', default=DEFAULT_XMPP_SERVER, type=str, help='Domain address')
@click.option('--max-slot-height', default=5, type=int, help='Max height of the slot')
@click.option('--slot-count', default=4, type=int, help='Slots count')
@click.option('--container-count', default=16, type=int, help='Container count')
@click.option("--max-containers-batch", default=1, type=int, help="max containers number in single batch")
@click.option("--min-arrival-delta", default=1, type=int, help="minimum arrival time delta between two batches in "
                                                               "seconds")
@click.option("--max-arrival-delta", default=10, type=int, help="maximum arrival time delta between two batches in "
                                                                "seconds")
@click.option("--min-departure-delta", default=5, type=int, help="minimum time delta between arrival and departure of "
                                                                 "container in seconds")
@click.option("--max-departure-delta", default=35, type=int, help="maximum time delta between arrival and departure of "
                                                                  "container in seconds")
@click.option("--departure-time-accuracy", default=0, type=int, help="accuracy of container departure time estimation "
                                                                     "in seconds")
def main(domain: str,
         max_slot_height: int,
         slot_count: int,
         container_count: int,
         max_containers_batch: int,
         min_arrival_delta: int,
         max_arrival_delta: int,
         min_departure_delta: int,
         max_departure_delta: int,
         departure_time_accuracy: int):
    agents = []
    try:
        df = DFAgent(domain, 'password1234')
        future = df.start()
        future.result()
        df.web.start(hostname="localhost", port="9999")
        agents.append(df)

        # Run port manager
        port_manager_agent_jid = f'port_manager@{domain}'
        run_port_manager_agent(port_manager_agent_jid)

        # Run slot managers
        for i in range(slot_count):
            agents.append(run_slot_manager_agent(str(i), domain, max_slot_height))

        # Run trucks managers and containers

        test_environment = TestEnvironment.instance()
        test_environment.setup(domain, max_slot_height, slot_count, container_count)
        containers_data = test_environment.prepare_test(max_containers_batch,
                                                        min_arrival_delta,
                                                        max_arrival_delta,
                                                        min_departure_delta,
                                                        max_departure_delta,
                                                        departure_time_accuracy)
        naive_moves = test_environment.get_moves_count_for_naive_method(containers_data)
        print(f"moves for naive method: {naive_moves}")
        truck_id = 0
        for container_data in containers_data:
            containers_jids = [container_data.jid]
            run_truck_agent(truck_id, domain, container_data.departure_time, containers_jids, port_manager_agent_jid)
            time_until_arrival = container_data.arrival_time - datetime.now()
            if time_until_arrival.seconds > 0 and time_until_arrival.days >= 0:
                asyncio.run(asyncio.sleep(time_until_arrival.seconds))
            agents.append(run_container_agent(container_data.jid, container_data.estimated_departure_time))
            truck_id += 1

        while True:
            sleep(1)

    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        for agent in agents:
            agent.stop()


if __name__ == "__main__":
    main()
