import asyncio
import time
from typing import Annotated
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp
from aioclock.triggers import Trigger

# service1.py
group = Group()

def dependency():
    """A simple dependency function that returns a greeting."""
    return "Hello, world!"

@group.task(trigger=Every(seconds=2))
def my_task(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a value from a dependency function.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print(f"Task 1: {val} - Thread ID: {threading.get_ident()}")
    time.sleep(1)
    return "Task 1 completed"

@group.task(trigger=Every(seconds=2.01))
def my_task2(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a value from a dependency function.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print(f"Task 2: {val} - Thread ID: {threading.get_ident()}")
    time.sleep(1)
    return "Task 2 completed"

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
def startup(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a welcome message when the application starts up.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print(f"Startup: {val} - Thread ID: {threading.get_ident()}")

@app.task(trigger=OnShutDown())
def shutdown(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a goodbye message when the application shuts down.

    Args:
        val (str): The value to print. This is a dependency that is injected into the function.
    """
    print(f"Shutdown: {val} - Thread ID: {threading.get_ident()}")

if __name__ == "__main__":
    asyncio.run(app.serve())