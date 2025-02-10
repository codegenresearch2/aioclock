import asyncio
import sys
import threading
from functools import wraps
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

T = TypeVar("T")
P = ParamSpec("P")

class AioClock:
    """
    AioClock is the main class that will be used to run the tasks.
    It will be responsible for running the tasks in the right order.
    """

    def __init__(self):
        """
        Initialize AioClock instance.
        No parameters are needed.
        """
        self._groups: list[Group] = []
        self._app_tasks: list[Task] = []

    @property
    def dependencies(self):
        """Dependencies provider that will be used to inject dependencies in tasks."""
        return get_provider()

    def override_dependencies(
        self, original: Callable[..., Any], override: Callable[..., Any]
    ) -> None:
        """Override a dependency with a new one.

        Args:
            original (Callable[..., Any]): The original dependency function.
            override (Callable[..., Any]): The new dependency function.
        """
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        """Include a group of tasks that will be run by AioClock.

        Args:
            group (Group): The group of tasks to include.
        """
        self._groups.append(group)
        return None

    def task(self, *, trigger: BaseTrigger):
        """Decorator to add a task to the AioClock instance.

        Args:
            trigger (BaseTrigger): The trigger for the task.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return func(*args, **kwargs)

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
        exclude_type = (
            exclude_type
            if exclude_type is not None
            else {Triggers.ON_START_UP, Triggers.ON_SHUT_DOWN}
        )

        return [task for task in self._tasks if task.trigger.type_ not in exclude_type]

    async def serve(self) -> None:
        """
        Serves AioClock
        Run the tasks in the right order.
        First, run the startup tasks, then run the tasks, and finally run the shutdown tasks.
        """

        self.include_group(Group(tasks=self._app_tasks))
        try:
            await asyncio.gather(
                *(threading.Thread(target=task.run).start() for task in self._get_startup_task()), return_exceptions=False
            )

            await asyncio.gather(
                *(threading.Thread(target=group.run).start() for group in self._get_tasks()), return_exceptions=False
            )
        finally:
            shutdown_tasks = self._get_shutdown_task()
            await asyncio.gather(*(threading.Thread(target=task.run).start() for task in shutdown_tasks), return_exceptions=False)