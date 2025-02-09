import asyncio
import sys
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject
from asyncer import asyncify

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

    Examples:
        Initialize the AioClock instance and add tasks:
        
        from aioclock import AioClock, Once
        import asyncio

        app = AioClock()

        @app.task(trigger=Once())
        async def main():
            print("Hello World")

        asyncio.run(app.serve())
        
    """

    def __init__(self):
        """
        Initialize AioClock instance.
        """
        self._groups: list[Group] = []
        self._app_tasks: list[Task] = []

    _groups: list[Group]
    """List of groups that will be run by AioClock."""

    _app_tasks: list[Task]
    """List of tasks that will be run by AioClock."""

    @property
    def dependencies(self):
        """
        Returns the dependencies provider for injecting dependencies in tasks.
        """
        return get_provider()

    def override_dependencies(
        self, original: Callable[..., Any], override: Callable[..., Any]
    ) -> None:
        """
        Override a dependency with a new one.

        Args:
            original (Callable[..., Any]): The original dependency function.
            override (Callable[..., Any]): The overriding dependency function.
        """
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        """
        Include a group of tasks that will be run by AioClock.

        Args:
            group (Group): The group of tasks to include.
        """
        self._groups.append(group)
        return None

    def task(self, *, trigger: BaseTrigger):
        """
        Decorator to add a task to the AioClock instance.

        Args:
            trigger (BaseTrigger): The trigger that defines when the task should run.

        Returns:
            Callable[P, Awaitable[T]]: The decorated function.
        """

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            task_instance = Task(
                func=inject(asyncify(wrapper), dependency_overrides_provider=self.dependencies),
                trigger=trigger,
            )
            self._app_tasks.append(task_instance)
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
                *(task.run() for task in self._get_startup_task()), return_exceptions=False
            )

            await asyncio.gather(
                *(group.run() for group in self._get_tasks()), return_exceptions=False
            )
        finally:
            shutdown_tasks = self._get_shutdown_task()
            await asyncio.gather(*(task.run() for task in shutdown_tasks), return_exceptions=False)