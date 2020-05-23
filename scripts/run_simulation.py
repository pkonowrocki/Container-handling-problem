import multiprocessing
import signal
import time
import sys
from datetime import datetime, timedelta
from typing import Sequence

import click

sys.path.extend(['.'])

from src.agents.container_agent import ContainerAgent
from src.agents.slot_manager_agent import SlotManagerAgent

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'
SLOT_MANAGERS_COUNT = 4
CONTAINERS_COUNT = 10


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
@click.option('--domain', default=XMPP_SERVER, type=str, help='Domain address')
@click.option('--max-slot-height', default=4, type=int, help='Max height of the slot')
def main(domain: str, max_slot_height: int):
    try:
        pool = multiprocessing.Pool(SLOT_MANAGERS_COUNT + CONTAINERS_COUNT, initializer=initializer)
        slot_manager_agents_jids = []

        for i in range(SLOT_MANAGERS_COUNT):
            slot_manager_agents_jids.append(f'slot_{i}@{domain}')
            pool.apply_async(run_slot_manager_agent, args=(i, domain, max_slot_height))

        time.sleep(10)
        for i in range(CONTAINERS_COUNT):
            pool.apply_async(run_container_agent,
                             args=(i, domain, datetime.now() + timedelta(0, 35), slot_manager_agents_jids))
            time.sleep(10)

        pool.close()
    except KeyboardInterrupt:
        print("Agent System terminated")
    finally:
        pool.terminate()
        pool.join()


if __name__ == "__main__":
    main()
