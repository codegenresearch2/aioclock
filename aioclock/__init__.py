from fast_depends import Depends
from crontab import CronTab

from aioclock.app import AioClock
from aioclock.group import Group
from aioclock.triggers import At, Every, Forever, Once, OnShutDown, OnStartUp
from aioclock.custom_types import EveryT, SecondT, MinuteT, HourT, PositiveNumber

__all__ = [
    "Depends",
    "Once",
    "OnStartUp",
    "OnShutDown",
    "Every",
    "Forever",
    "Group",
    "AioClock",
    "At",
    "Cron",
]

__version__ = "0.1.1"

class Cron:
    """\n    Cron job trigger.\n\n    This class allows the user to schedule tasks based on cron job syntax.\n\n    Attributes:\n        cron_expression (str): The cron job expression.\n    """

    def __init__(self, cron_expression: str):
        """\n        Initialize the Cron job trigger.\n\n        Args:\n            cron_expression (str): The cron job expression.\n        """
        self.cron_expression = cron_expression

    def validate_expression(self):
        """\n        Validate the cron job expression.\n\n        Raises:\n            ValueError: If the cron job expression is invalid.\n        """
        cron = CronTab(self.cron_expression)
        if not cron.is_valid():
            raise ValueError("Invalid cron job expression")

    def __str__(self):
        """\n        Return the cron job expression as a string.\n\n        Returns:\n            str: The cron job expression.\n        """
        return self.cron_expression

# Added cron job support
# Improved code documentation
# Maintained consistent trigger functionality