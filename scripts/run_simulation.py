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

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent, SlotJid
from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = 'host.docker.internal'


def run_slot_manager_agent(slot_id: str, domain: str, max_height: int):
    slot_manager_agent = SlotManagerAgent(f'slot_{slot_id}@{domain}', 'slot_password', slot_id, max_height)
    future = slot_manager_agent.start()
    future.result()
    return slot_manager_agent


def run_container_agent(container_id: str, domain: str, departure_time: datetime,
                        slot_manager_agents_jids: Sequence[JID]):
    container_agent = ContainerAgent(f'container_{container_id}@{domain}', 'container_password',
                                     slot_manager_agents_jids, departure_time)
    container_agent.start()
    return container_agent


@click.command()
@click.option('--domain', default=DEFAULT_XMPP_SERVER, type=str, help='Domain address')
@click.option('--max-slot-height', default=5, type=int, help='Max height of the slot')
@click.option('--slot-count', default=4, type=int, help='Slots count')
@click.option('--container-count', default=16, type=int, help='Container count')
def main(domain: str, max_slot_height: int, slot_count: int, container_count: int):
    agents = []
    try:
        slot_manager_agents_jids: List[SlotJid] = []

        df = DFAgent(f'dfagent@{domain}', 'password1234')
        future = df.start()
        future.result()
        DFService.init(df)
        df.web.start(hostname="localhost", port="9999")
        agents.append(df)

        for i in range(slot_count):
            slot_manager_agents_jids.append(SlotJid(i, f'slot_{i}@{domain}'))
            agents.append(run_slot_manager_agent(i, domain, max_slot_height))

        asyncio.run(asyncio.sleep(3))
        for i in range(container_count):
            agents.append(run_container_agent(i, domain, datetime.now() + timedelta(0, 40), slot_manager_agents_jids))
            asyncio.run(asyncio.sleep(3))

        while True:
            asyncio.run(asyncio.sleep(1))

    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        for agent in agents:
            agent.stop()


if __name__ == "__main__":
    main()
