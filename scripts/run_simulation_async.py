import asyncio
import multiprocessing
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

DEFAULT_XMPP_SERVER = 'host.docker.internal'


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
    future = port_manager_agent.start()
    future.result()


def initializer():
    """Ignore SIGINT in child workers."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


@click.command()
@click.option('--domain', default=DEFAULT_XMPP_SERVER, type=str, help='Domain address')
@click.option('--max-slot-height', default=5, type=int, help='Max height of the slot')
@click.option('--slot-count', default=4, type=int, help='Slots count')
@click.option('--container-count', default=16, type=int, help='Container count')
def main(domain: str, max_slot_height: int, slot_count: int, container_count: int):
    agents = []
    pool = multiprocessing.Pool(slot_count + 2 * container_count, initializer=initializer)
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
            pool.apply_async(run_slot_manager_agent, args=(str(i), domain, max_slot_height))

        test_environment = TestEnvironment.instance()
        test_environment.setup(domain, max_slot_height, slot_count, container_count)
        containers_data = test_environment.prepare_test(1)
        naive_moves = test_environment.get_moves_count_for_naive_method(containers_data)
        print(f"moves for naive method: {naive_moves}")
        truck_id = 0
        # Run truck managers and containers
        for container_data in containers_data:
            containers_jids = [container_data.jid]
            pool.apply_async(run_truck_agent, args=(truck_id, domain, container_data.departure_time, containers_jids, port_manager_agent_jid))
            time_until_arrival = container_data.arrival_time - datetime.now()
            if time_until_arrival.seconds > 0:
                asyncio.run(asyncio.sleep(time_until_arrival.seconds))
            pool.apply_async(run_container_agent, args=(container_data.jid, container_data.departure_time))
            truck_id += 1

        while True:
            sleep(1)

    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        pool.terminate()
        pool.join()


if __name__ == "__main__":
    main()
