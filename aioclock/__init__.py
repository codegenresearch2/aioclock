import asyncio
from typing import Optional

from fast_depends import Depends
from aioclock.app import AioClock
from aioclock.group import Group
from aioclock.triggers import At, Every, Forever, Once, OnShutDown, OnStartUp
from aioclock.custom_types import EveryT, HourT, MinuteT, SecondT

# Improved documentation
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
    "Cron",  # Added Cron for cron job support
]

__version__ = "0.1.1"

# Added Cron trigger for cron job support
class Cron:
    """Cron job trigger."""

    def __init__(self, minute: MinuteT = "*", hour: HourT = "*", day_of_week: Optional[EveryT] = None):
        """\n        Initialize the Cron trigger.\n\n        :param minute: Minute of the hour (0-59) or "*" for every minute.\n        :param hour: Hour of the day (0-23) or "*" for every hour.\n        :param day_of_week: Day of the week (e.g., "every monday", "every day") or None for every day.\n        """
        self.minute = minute
        self.hour = hour
        self.day_of_week = day_of_week

    async def __call__(self):
        """\n        Check if the cron job should trigger.\n\n        :return: True if the cron job should trigger, False otherwise.\n        """
        # Implementation depends on the specific cron job scheduling logic
        pass

# Rewritten code with improved documentation and cron job support
def more_useless_than_me():
    """\n    A dependency function that does not do anything useful.\n\n    :return: A useless string.\n    """
    return "I'm a dependency. I'm more useless than a screen door on a submarine."

app = AioClock()
group = Group()

@group.task(trigger=Every(seconds=10))
async def every():
    """\n    A task that prints a message every 10 seconds.\n    """
    print("Every 10 seconds, I make a quantum leap. Where will I land next?")

@group.task(trigger=Every(seconds=5))
def even_sync_works():
    """\n    A synchronous task that prints a message every 5 seconds.\n    """
    print("I'm a synchronous task. I work even in async world.")

@group.task(trigger=At(tz="UTC", hour=0, minute=0, second=0))
async def at():
    """\n    A task that prints a message at midnight UTC.\n    """
    print("When the clock strikes midnight... I turn into a pumpkin. Just kidding, I run this task!")

@group.task(trigger=Forever())
async def forever(val: str = Depends(more_useless_than_me)):
    """\n    A task that prints a heartbeat message every 2 seconds and asserts a useless dependency.\n\n    :param val: A useless dependency value.\n    """
    await asyncio.sleep(2)
    print("Heartbeat detected. Still not a zombie. Will check again in a bit.")
    assert val == "I'm a dependency. I'm more useless than a screen door on a submarine."

@group.task(trigger=Once())
async def once():
    """\n    A task that prints a message once.\n    """
    print("Just once, I get to say something. Here it goes... I love lamp.")

@group.task(trigger=Cron(minute="*/5"))  # Example of using Cron trigger every 5 minutes
async def cron_example():
    """\n    An example task that prints a message every 5 minutes using the Cron trigger.\n    """
    print("I'm a cron job example! I run every 5 minutes.")

app.include_group(group)

@app.task(trigger=OnStartUp())
async def startup():
    """\n    A task that prints a welcome message on application start up.\n    """
    print("Welcome to the Async Chronicles! Did you know a group of unicorns is called a blessing? Well, now you do!")

@app.task(trigger=OnShutDown())
async def shutdown():
    """\n    A task that prints a goodbye message on application shut down.\n    """
    print("Going offline. Remember, if your code is running, you better go catch it!")

if __name__ == "__main__":
    asyncio.run(app.serve())