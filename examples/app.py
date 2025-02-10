import asyncio
from functools import wraps
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp
from aioclock.triggers import Trigger
from aioclock.utils import run_sync

# service1.py
group = Group()

def dependency():
    """A simple dependency function that returns a greeting."""
    return "Hello, world!"

def sync_wrapper(func):
    """A decorator to run synchronous functions in an asynchronous context."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_sync(func, *args, **kwargs)
    return wrapper

@group.task(trigger=Every(seconds=1), max_capacity=1)
async def my_task(val: str = Depends(sync_wrapper(dependency))):
    """A task that prints a value from a dependency function.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print(val)

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
async def startup(val: str = Depends(sync_wrapper(dependency))):
    """A task that prints a welcome message when the application starts up.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print("Welcome!")

@app.task(trigger=OnShutDown())
async def shutdown(val: str = Depends(sync_wrapper(dependency))):
    """A task that prints a goodbye message when the application shuts down.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print("Bye!")

if __name__ == "__main__":
    asyncio.run(app.serve())