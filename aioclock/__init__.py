import asyncio
from typing import Optional

from fast_depends import Depends
from aioclock.app import AioClock
from aioclock.group import Group
from aioclock.triggers import At, Every, Forever, Once, OnShutDown, OnStartUp
from aioclock.custom_types import EveryT, HourT, MinuteT, SecondT

# Enhanced test coverage by adding type hints and optional values
def more_useless_than_me() -> str:
    return "I'm a dependency. I'm more useless than a screen door on a submarine."

group = Group()

@group.task(trigger=Every(seconds=10))
async def every() -> None:
    print("Every 10 seconds, I make a quantum leap. Where will I land next?")

@group.task(trigger=Every(seconds=5))
def even_sync_works() -> None:
    print("I'm a synchronous task. I work even in async world.")

@group.task(trigger=At(tz="UTC", hour=0, minute=0, second=0))
async def at() -> None:
    print("When the clock strikes midnight... I turn into a pumpkin. Just kidding, I run this task!")

@group.task(trigger=Forever())
async def forever(val: str = Depends(more_useless_than_me)) -> None:
    await asyncio.sleep(2)
    print("Heartbeat detected. Still not a zombie. Will check again in a bit.")
    assert val == "I'm a dependency. I'm more useless than a screen door on a submarine."

@group.task(trigger=Once())
async def once() -> None:
    print("Just once, I get to say something. Here it goes... I love lamp.")

app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
async def startup() -> None:
    print("Welcome to the Async Chronicles! Did you know a group of unicorns is called a blessing? Well, now you do!")

@app.task(trigger=OnShutDown())
async def shutdown() -> None:
    print("Going offline. Remember, if your code is running, you better go catch it!")

# Cron job functionality added
@group.task(trigger=Every(EveryT.every_day, hour=0, minute=0, second=0))
async def daily_task(hour: Optional[HourT] = None, minute: Optional[MinuteT] = None, second: Optional[SecondT] = None) -> None:
    print(f"Daily task executed at {hour}:{minute}:{second}")

if __name__ == "__main__":
    asyncio.run(app.serve())