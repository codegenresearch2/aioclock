import asyncio
from typing import Callable, Optional

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
def default_dependency() -> str:
    """Default dependency function that returns a greeting."""
    return "Hello, world!"

class Service:
    """Service class that encapsulates tasks and dependencies."""

    def __init__(self, dependency: Optional[Callable[[], str]] = None):
        self.group = Group()
        self.dependency = dependency or default_dependency

    @group.task(trigger=Every(seconds=1))
    async def my_task(self, val: str = Depends(dependency)):
        """Task that prints the value returned by the dependency function."""
        print(val)

# app.py
class App:
    """Main application class that manages the service and tasks."""

    def __init__(self, service: Service):
        self.app = AioClock()
        self.service = service
        self.app.include_group(service.group)

    @app.task(trigger=OnStartUp())
    async def startup(self, val: str = Depends(service.dependency)):
        """Startup task that prints a welcome message and the value returned by the dependency function."""
        print("Welcome!")
        print(val)

    @app.task(trigger=OnShutDown())
    async def shutdown(self, val: str = Depends(service.dependency)):
        """Shutdown task that prints a goodbye message and the value returned by the dependency function."""
        print("Bye!")
        print(val)

    async def serve(self):
        """Starts the application."""
        await self.app.serve()

if __name__ == "__main__":
    service = Service()
    app = App(service)
    asyncio.run(app.serve())