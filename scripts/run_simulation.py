import asyncio
import multiprocessing
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Sequence, List, Awaitable

import click
from aioxmpp import JID

from src.agents.DFAgent import DFService, DFAgent

from src.agents.port_manager_agent import PortManagerAgent
from src.agents.truck_agent import TruckAgent
from src.utils.test_environment import TestEnvironment

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent, SlotJid
from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = '192.168.0.24'


def run_slot_manager_agent(slot_id: str, domain: str, max_height: int):
    slot_manager_agent = SlotManagerAgent(f'slot_{slot_id}@{domain}', 'slot_password', slot_id, max_height)
    future = slot_manager_agent.start()
    future.result()
    return slot_manager_agent


def run_container_agent(container_jid: str, departure_time: datetime,
                        slot_manager_agents_jids: Sequence[JID]):
    container_agent = ContainerAgent(container_jid, 'container_password',
                                     slot_manager_agents_jids, departure_time)
    container_agent.start()
    return container_agent


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
    agents = []
    try:
        slot_manager_agents_jids: List[SlotJid] = []
        port_manager_agent_jid = f'port_manager@{domain}'

        df = DFAgent(f'dfagent@{domain}', 'password1234')
        future = df.start()
        future.result()
        DFService.init(df)
        df.web.start(hostname="localhost", port="9999")
        agents.append(df)

        # Run port manager
        run_port_manager_agent(port_manager_agent_jid)

        # Run slot managers
        for i in range(slot_count):
            slot_manager_agents_jids.append(SlotJid(i, f'slot_{i}@{domain}'))
            agents.append(run_slot_manager_agent(i, domain, max_slot_height))
        asyncio.run(asyncio.sleep(3))
        # for i in range(container_count):
        #     agents.append(run_container_agent(i, domain, datetime.now() + timedelta(0, 40), slot_manager_agents_jids))
        #     asyncio.run(asyncio.sleep(3))

        # Run trucks managers and containers

        test_environment = TestEnvironment(domain, max_slot_height, slot_count, container_count)
        containers_data = test_environment.prepare_test(1)
        naive_moves = test_environment.get_moves_count_for_naive_method(containers_data)
        print(f"moves for naive method: {naive_moves}")
        truck_id = 0
        for container_data in containers_data:
            containers_jids = [container_data.jid]
            run_truck_agent(truck_id, domain, container_data.departure_time, containers_jids, port_manager_agent_jid)
            time_until_arrival = container_data.arrival_time - datetime.now()
            if time_until_arrival.seconds > 0:
                asyncio.run(asyncio.sleep(time_until_arrival.seconds))
            agents.append(run_container_agent(container_data.jid, container_data.departure_time, slot_manager_agents_jids))
            truck_id += 1

        while True:
            asyncio.run(asyncio.sleep(1))

    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        for agent in agents:
            agent.stop()


if __name__ == "__main__":
    main()
