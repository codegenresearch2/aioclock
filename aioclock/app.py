import asyncio
import sys
from functools import wraps
import threading
from typing import Any, Awaitable, Callable, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject

from aioclock.custom_types import Triggers
from aioclock.group import Group, Task
from aioclock.provider import get_provider
from aioclock.triggers import BaseTrigger
from aioclock.utils import flatten_chain

T = TypeVar('T')
P = ParamSpec('P')

class AioClock:
    """\n    AioClock is the main class that will be used to run the tasks.\n    It will be responsible for running the tasks in the right order.\n    """

    def __init__(self):
        """\n        Initialize AioClock instance.\n        No parameters are needed.\n        """
        self._groups: list[Group] = []
        self._app_tasks: list[Task] = []

    @property
    def dependencies(self):
        """Dependencies provider that will be used to inject dependencies in tasks."""
        return get_provider()

    def override_dependencies(self, original: Callable[..., Any], override: Callable[..., Any]) -> None:
        """\n        Override a dependency with a new one.\n\n        Args:\n            original (Callable[..., Any]): The original dependency function.\n            override (Callable[..., Any]): The new dependency function.\n        """
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        """\n        Include a group of tasks that will be run by AioClock.\n\n        Args:\n            group (Group): The group of tasks to include.\n        """
        self._groups.append(group)
        return None

    def task(self, *, trigger: BaseTrigger):
        """\n        Decorator to add a task to the AioClock instance.\n\n        Args:\n            trigger (BaseTrigger): The trigger for the task.\n        """
        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # Use a thread to run the synchronous function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(func(*args, **kwargs))
                finally:
                    loop.close()

            self._app_tasks.append(
                Task(
                    func=inject(wrapper, dependency_overrides_provider=get_provider()),
                    trigger=trigger,
                )
            )
            return wrapper

        return decorator

    @property
    def _tasks(self) -> list[Task]:
        result = flatten_chain([group._tasks for group in self._groups])
        return result

    def _get_shutdown_task(self) -> list[Task]:
        return [task for task in self._tasks if task.trigger.type_ == Triggers.ON_SHUT_DOWN]

    def _get_startup_task(self) -> list[Task]:
        return [task for task in self._tasks if task.trigger.type_ == Triggers.ON_START_UP]

    def _get_tasks(self, exclude_type: Union[set[Triggers], None] = None) -> list[Task]:
        exclude_type = exclude_type if exclude_type is not None else {Triggers.ON_START_UP, Triggers.ON_SHUT_DOWN}
        return [task for task in self._tasks if task.trigger.type_ not in exclude_type]

    async def serve(self) -> None:
        """\n        Serves AioClock. Run the tasks in the right order.\n        First, run the startup tasks, then run the tasks, and finally run the shutdown tasks.\n        """
        self.include_group(Group(tasks=self._app_tasks))
        try:
            await asyncio.gather(*(task.run() for task in self._get_startup_task()), return_exceptions=False)

            # Use threading to run tasks concurrently
            threads = [threading.Thread(target=asyncio.run, args=(group.run(),)) for group in self._get_tasks()]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        finally:
            shutdown_tasks = self._get_shutdown_task()
            await asyncio.gather(*(task.run() for task in shutdown_tasks), return_exceptions=False)