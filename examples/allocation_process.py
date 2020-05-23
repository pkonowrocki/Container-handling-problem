import asyncio
from datetime import datetime, timedelta

from src.agents.container_agent import ContainerAgent
from src.agents.slot_manager_agent import SlotManagerAgent

XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'
CONTAINERS_COUNT = 8
SLOTS_COUNT = 4
MAX_HEIGHT = 4


async def run_container(i: int, delay: int):
    await asyncio.sleep(delay)
    departure_time = datetime.now() + timedelta(0, 20)
    container_agent = ContainerAgent(f'container_{i}@{XMPP_SERVER}', 'container_password', slot_manager_agents_jids,
                                     departure_time)
    future = container_agent.start()
    future.result()


if __name__ == "__main__":
    slot_manager_agents_jids = [f'slot_{i}@{XMPP_SERVER}' for i in range(SLOTS_COUNT)]

    for i in range(SLOTS_COUNT):
        slot_manager_agent = SlotManagerAgent(f'slot_{i}@{XMPP_SERVER}', 'slot_password', str(i), MAX_HEIGHT)
        future = slot_manager_agent.start()
        future.result()

    for i in range(CONTAINERS_COUNT):
        asyncio.run(run_container(i, i * 10))
