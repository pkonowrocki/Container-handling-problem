from enum import IntEnum


class Performative(IntEnum):
    AGREE = 0
    REFUSE = 1
    NOT_UNDERSTOOD = 2
    INFORM = 3
    FAILURE = 4
    REQUEST = 5
    PROPOSE = 6
    CFP = 7
    ACCEPT_PROPOSAL = 8
    REJECT_PROPOSAL = 9
