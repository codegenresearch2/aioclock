import asyncio
import sys
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, Union, Optional

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
import anyio

T = TypeVar("T")
P = ParamSpec("P")


class AioClock:
    """
    AioClock is the main class that will be used to run the tasks.
    It will be responsible for running the tasks in the right order.

    Example:
        \"\"\"python
        from aioclock import AioClock, Once
        app = AioClock()

        @app.task(trigger=Once())
        async def main():
            print("Hello World")
        \"\"\"

    To run the aioclock final app simply do:

    Example:
        \"\"\"python
        from aioclock import AioClock, Once
        import asyncio

        app = AioClock()

        # whatever next comes here
        asyncio.run(app.serve())
        \"\"\"
    """

    def __init__(self, capacity_limiter: Optional[anyio.CapacityLimiter] = None):
        """
        Initialize AioClock instance.
        :param capacity_limiter: Optional capacity limiter for managing task execution.
        """
        self.capacity_limiter = capacity_limiter
        self._groups: list[Group] = []
        self._app_tasks: list[Task] = []

    _groups: list[Group]
    """List of groups that will be run by AioClock."""

    _app_tasks: list[Task]
    """List of tasks that will be run by AioClock."""

    @property
    def dependencies(self):
        """Dependencies provider that will be used to inject dependencies in tasks."""
        return get_provider()

    def override_dependencies(self,
                              original: Callable[..., Any],
                              override: Callable[..., Any]):
        """Override a dependency with a new one.

        Example:
            \"\"\"python
            from aioclock import AioClock

            def original_dependency():
                return 1

            def new_dependency():
                return 2

            app = AioClock()
            app.override_dependencies(original=original_dependency, override=new_dependency)
            \"\"\"
        """
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        """Include a group of tasks that will be run by AioClock.

        Example:
            \"\"\"python
            from aioclock import AioClock, Group, Once

            app = AioClock()

            group = Group()
            @group.task(trigger=Once())
            async def main():
                print("Hello World")

            app.include_group(group)
            \"\"\"
        """
        self._groups.append(group)
        return None

    def task(self, *, trigger: BaseTrigger):
        """Decorator to add a task to the AioClock instance.

        Example:

            \"\"\"python
            from aioclock import AioClock, Once

            app = AioClock()

            @app.task(trigger=Once())
            async def main():
                print("Hello World")
            \"\"\"
        """

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await func(*args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                self._app_tasks.append(
                    Task(
                        func=inject(wrapper, dependency_overrides_provider=get_provider()),
                        trigger=trigger,
                    )
                )
            else:
                self._app_tasks.append(
                    Task(
                        func=inject(anyio.asyncify(wrapper), dependency_overrides_provider=get_provider()),
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

        startup_group = Group()
        startup_group.add_tasks(self._get_startup_task())
        self.include_group(startup_group)

        normal_group = Group()
        normal_group.add_tasks(self._get_tasks())
        self.include_group(normal_group)

        shutdown_group = Group()
        shutdown_group.add_tasks(self._get_shutdown_task())
        self.include_group(shutdown_group)

        try:
            await asyncio.gather(
                *(group.run() for group in [startup_group, normal_group, shutdown_group]),
                return_exceptions=False,
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.gather(
                *(group.run() for group in [shutdown_group]),
                return_exceptions=False,
            )
            raise
