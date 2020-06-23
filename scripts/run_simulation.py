import multiprocessing
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Sequence, List

import click
from aioxmpp import JID

from src.agents.port_manager_agent import PortManagerAgent
from src.agents.truck_agent import TruckAgent

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent, SlotJid
from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = 'localhost'


def run_slot_manager_agent(slot_id: str, domain: str, max_height: int):
    slot_manager_agent = SlotManagerAgent(f'slot_{slot_id}@{domain}', 'slot_password', slot_id, max_height)
    future = slot_manager_agent.start()
    future.result()


def run_container_agent(container_jid: str, departure_time: datetime,
                        slot_manager_agents_jids: Sequence[JID]):
    container_agent = ContainerAgent(container_jid, 'container_password',
                                     slot_manager_agents_jids, departure_time)
    container_agent.start()


def run_truck_agent(truck_id: str, domain: str, arrival_time: datetime, containers_jids: Sequence[str],
                    port_manager_agent_jid: str):
    truck_agent = TruckAgent(f'truck_{truck_id}@{domain}', 'truck_password', containers_jids, arrival_time,
                             port_manager_agent_jid)
    truck_agent.start()


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
def main(domain: str, max_slot_height: int, slot_count: int, container_count: int):
    try:
        pool = multiprocessing.Pool(slot_count + container_count, initializer=initializer)
        slot_manager_agents_jids: List[SlotJid] = []
        port_manager_agent_jid = f'port_manager@{domain}'

        # Run port manager
        run_port_manager_agent(port_manager_agent_jid)

        # Run slot managers
        for i in range(slot_count):
            slot_manager_agents_jids.append(SlotJid(i, f'slot_{i}@{domain}'))
            pool.apply_async(run_slot_manager_agent, args=(i, domain, max_slot_height))
        time.sleep(5)

        # Run trucks managers and containers
        containers_ids = range(container_count)
        truck_id = 0
        for truck_containers in zip(containers_ids[0::2], containers_ids[1::2]):
            departure_time = datetime.now() + timedelta(seconds=40)
            containers_jids = [f'container_{container_id}@{domain}' for container_id in truck_containers]
            pool.apply_async(run_truck_agent,
                             args=(truck_id, domain, departure_time, containers_jids, port_manager_agent_jid))

            for container_jid in containers_jids:
                pool.apply_async(run_container_agent,
                                 args=(container_jid, departure_time, slot_manager_agents_jids))
                time.sleep(3)
            truck_id += 1

        while True:
            time.sleep(1)

        # pool.close()
    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        pool.terminate()
        pool.join()


if __name__ == "__main__":
    main()
