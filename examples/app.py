import asyncio
import threading
from typing import Callable, Optional

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# Define the group globally
group = Group()

# Define the default dependency function
def default_dependency() -> str:
    """Default dependency function that returns a greeting."""
    return "Hello, world!"

# Define the tasks outside of the classes
@group.task(trigger=Every(seconds=2))
async def my_async_task(val: str = Depends(default_dependency)):
    """Asynchronous task that prints the value returned by the dependency function."""
    print(f"Async Task - Thread: {threading.current_thread().name}, Value: {val}")

@group.task(trigger=Every(seconds=2.01))
def my_sync_task(val: str = Depends(default_dependency)) -> str:
    """Synchronous task that prints the value returned by the dependency function and returns a string."""
    print(f"Sync Task - Thread: {threading.current_thread().name}, Value: {val}")
    return "Sync Task Completed"

# Define the main application class
class App:
    """Main application class that manages the tasks."""

    def __init__(self):
        self.app = AioClock()
        self.app.include_group(group)

    @app.task(trigger=OnStartUp())
    async def startup(self, val: str = Depends(default_dependency)):
        """Startup task that prints a welcome message and the value returned by the dependency function."""
        print("Welcome!")
        print(f"Startup Task - Thread: {threading.current_thread().name}, Value: {val}")

    @app.task(trigger=OnShutDown())
    async def shutdown(self, val: str = Depends(default_dependency)):
        """Shutdown task that prints a goodbye message and the value returned by the dependency function."""
        print("Bye!")
        print(f"Shutdown Task - Thread: {threading.current_thread().name}, Value: {val}")

    async def serve(self):
        """Starts the application."""
        await self.app.serve()

if __name__ == "__main__":
    app = App()
    asyncio.run(app.serve())