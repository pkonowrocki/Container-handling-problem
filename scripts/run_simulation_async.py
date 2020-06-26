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

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent
from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = 'localhost'


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

        sleep(5)
        # Run truck managers and containers
        for i in range(container_count):
            departure_time = datetime.now() + timedelta(seconds=20)
            container_jid = f'container_{i}@{domain}'
            pool.apply_async(run_container_agent, args=(container_jid, departure_time))
            pool.apply_async(run_truck_agent, args=(i, domain, departure_time, [container_jid], port_manager_agent_jid))
            sleep(3)

        while True:
            sleep(1)

    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        pool.terminate()
        pool.join()


if __name__ == "__main__":
    main()
