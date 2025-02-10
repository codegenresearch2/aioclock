import asyncio
import threading
from typing import Annotated
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp
import time

# service1.py
group = Group()

def dependency():
    """A dependency function that returns the thread context."""
    return f"Thread ID: {threading.current_thread().ident}"

@group.task(trigger=Every(seconds=2))
def sync_task_1(val: Annotated[str, Depends(dependency)] = "Default Value"):
    """A synchronous task that prints a value from a dependency function."""
    print(f"Sync Task 1 - {val}")
    time.sleep(1)

@group.task(trigger=Every(seconds=2.01))
def sync_task_2(val: Annotated[str, Depends(dependency)] = "Default Value"):
    """A synchronous task that prints a value from a dependency function and returns a value."""
    print(f"Sync Task 2 - {val}")
    time.sleep(1)
    return "Sync Task 2 Completed"

@group.task(trigger=Every(seconds=2.02))
async def async_task(val: Annotated[str, Depends(dependency)] = "Default Value"):
    """An asynchronous task that prints a value from a dependency function."""
    print(f"Async Task - {val}")
    await asyncio.sleep(1)

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
def startup_task(val: Annotated[str, Depends(dependency)] = "Default Value"):
    """A synchronous task that prints a welcome message when the application starts up."""
    print(f"Startup Task - {val}")

@app.task(trigger=OnShutDown())
def shutdown_task(val: Annotated[str, Depends(dependency)] = "Default Value"):
    """A synchronous task that prints a goodbye message when the application shuts down."""
    print(f"Shutdown Task - {val}")

if __name__ == "__main__":
    asyncio.run(app.serve())