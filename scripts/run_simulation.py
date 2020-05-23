import multiprocessing
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Sequence

import click

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent
from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'


def run_slot_manager_agent(slot_id: str, domain: str, max_height: int):
    slot_manager_agent = SlotManagerAgent(f'slot_{slot_id}@{domain}', 'slot_password', slot_id, max_height)
    future = slot_manager_agent.start()
    future.result()


def run_container_agent(container_id: str, domain: str, departure_time: datetime,
                        slot_manager_agents_jids: Sequence[str]):
    container_agent = ContainerAgent(f'container_{container_id}@{domain}', 'container_password',
                                     slot_manager_agents_jids, departure_time)
    container_agent.start()


def initializer():
    """Ignore SIGINT in child workers."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


@click.command()
@click.option('--domain', default=DEFAULT_XMPP_SERVER, type=str, help='Domain address')
@click.option('--max-slot-height', default=4, type=int, help='Max height of the slot')
@click.option('--slot-count', default=5, type=int, help='Slots count')
@click.option('--container-count', default=2, type=int, help='Container count')
def main(domain: str, max_slot_height: int, slot_count: int, container_count: int):
    try:
        pool = multiprocessing.Pool(slot_count + container_count, initializer=initializer)
        slot_manager_agents_jids = []

        for i in range(slot_count):
            slot_manager_agents_jids.append(f'slot_{i}@{domain}')
            pool.apply_async(run_slot_manager_agent, args=(i, domain, max_slot_height))

        time.sleep(10)
        for i in range(container_count):
            pool.apply_async(run_container_agent,
                             args=(i, domain, datetime.now() + timedelta(0, 35), slot_manager_agents_jids))
            time.sleep(10)

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
