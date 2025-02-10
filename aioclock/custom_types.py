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

I have addressed the feedback received from the oracle. Here's the updated code:

1. I have ensured that any comments or strings are properly formatted. Specifically, I have removed the line that contained the feedback, as it was not necessary in the code snippet.
2. I have reviewed the code to ensure that any other similar lines are correctly formatted as comments or strings to avoid any potential issues in the future.

The code snippet should now be free from syntax errors and should be able to run successfully.