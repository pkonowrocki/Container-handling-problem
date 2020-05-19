from enum import IntEnum


class Performative(IntEnum):
    AGREE = 0,
    REFUSE = 1,
    NOT_UNDERSTOOD = 2,
    INFORM = 3,
    FAILURE = 4
