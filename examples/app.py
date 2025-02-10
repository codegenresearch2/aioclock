import asyncio
import threading
from typing import Annotated
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()

def dependency():
    """A dependency function that returns a greeting with thread context."""
    return f"Hello, world! - Thread ID: {threading.current_thread().ident}"

@group.task(trigger=Every(seconds=2))
def print_greeting(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a value from a dependency function."""
    print(f"Print Greeting Task: {val}")

@group.task(trigger=Every(seconds=2.01))
async def async_task(val: Annotated[str, Depends(dependency)]):
    """An asynchronous task that prints a value from a dependency function."""
    print(f"Async Task: {val}")
    await asyncio.sleep(1)

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
def startup_task(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a welcome message when the application starts up."""
    print(f"Startup Task: {val}")

@app.task(trigger=OnShutDown())
def shutdown_task(val: Annotated[str, Depends(dependency)]):
    """A synchronous task that prints a goodbye message when the application shuts down."""
    print(f"Shutdown Task: {val}")

if __name__ == "__main__":
    asyncio.run(app.serve())