from aioxmpp import JID


def jid_to_str(jid: JID) -> str:
    return f'{jid.localpart}@{jid.domain}{f"{jid.resource}" if jid.resource is not None else ""}'
