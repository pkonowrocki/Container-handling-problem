import sys
import time

import click

sys.path.extend(['.'])

from src.agents.slot_manager_agent import SlotManagerAgent

DEFAULT_XMPP_SERVER = 'andzelika-thinkpad-t470s-w10dg'


@click.command()
@click.option('--slot-id', required=True, type=str, help='Unique id of the slot')
@click.option('--domain', default=DEFAULT_XMPP_SERVER, type=str, help='Domain address')
@click.option('--max-height', default=4, type=int, help='Max height of the slot')
def run_slot_manager_agent(slot_id: str, domain: str, max_height: int):
    slot_manager_agent = SlotManagerAgent(f'slot_{slot_id}@{domain}', 'slot_password', slot_id, max_height)
    slot_manager_agent.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    slot_manager_agent.stop()


if __name__ == "__main__":
    run_slot_manager_agent()
