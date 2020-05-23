from enum import IntEnum


class Performative(IntEnum):
    ACCEPT_PROPOSAL = 0
    AGREE = 1
    CFP = 3
    CONFIRM = 4
    DISCONFIRM = 5
    FAILURE = 6
    INFORM = 7
    INFORM_IF = 8
    INFORM_REF = 9
    NOT_UNDERSTOOD = 10
    PROPOSE = 11
    QUERY_IF = 12
    QUERY_REF = 13
    REFUSE = 14
    REJECT_PROPOSAL = 15
    REQUEST = 16
    REQUEST_WHEN = 17
    REQUEST_WHENEVER = 18
    SUBSCRIBE = 19
    PROXY = 20
    PROPAGATE = 21
    UNKNOWN = -1
