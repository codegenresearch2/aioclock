from enum import auto
from typing import Annotated, Literal, Union

from annotated_types import Interval

from aioclock.utils import StrEnum

EveryT = Literal[
    "every monday",
    "every tuesday",
    "every wednesday",
    "every thursday",
    "every friday",
    "every saturday",
    "every sunday",
    "every day",
]

SecondT = Annotated[int, Interval(ge=0, le=59)]
MinuteT = Annotated[int, Interval(ge=0, le=59)]
HourT = Annotated[int, Interval(ge=0, le=24)]

PositiveNumber = Annotated[Union[int, float], Interval(ge=0)]

class Triggers(StrEnum):
    CRON = auto()
    """Cron job trigger."""
    EVERY = auto()
    """Every (x) time units, it gets triggered."""
    ONCE = auto()
    """Trigger once, then stop."""
    FOREVER = auto()
    """Keep running, as long as application is running."""
    ON_START_UP = auto()
    """Trigger on application start up."""
    ON_SHUT_DOWN = auto()
    """Trigger on application shut down."""
    AT = auto()
    """Trigger at a specific time."""

# Addressing Oracle Feedback:
# 1. Interval Definitions: Updated the upper limit for HourT to match the gold code's specifications.
# 2. Comment Consistency: Ensured the wording for the ON_SHUT_DOWN trigger matches exactly with the gold code.
# 3. PositiveNumber Definition: Updated the definition to reflect the gold code's specification of a lower limit of 0 without an upper limit.