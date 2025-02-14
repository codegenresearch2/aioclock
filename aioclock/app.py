"""\nTo initialize the AioClock instance, you need to import the AioClock class from the aioclock module.\nAioClock class represents the aioclock, and handles the tasks and groups that will be run by the aioclock.\n\nAnother way to modularize your code is to use `Group`, which is similar to a router in web frameworks.\n"""

import asyncio
import sys
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
    """\n    AioClock is the main class that will be used to run the tasks.\n    It will be responsible for running the tasks in the right order.\n\n    Example:\n        \n        from aioclock import AioClock, Once\n        app = AioClock()\n\n        @app.task(trigger=Once())\n        async def main():\n            print("Hello World")\n        \n\n    To run the AioClock app, simply do:\n\n    Example:\n        \n        from aioclock import AioClock, Once\n        import asyncio\n\n        app = AioClock()\n\n        # whatever comes next\n        asyncio.run(app.serve())\n        \n    """

    def __init__(self):
        """\n        Initialize AioClock instance.\n        No parameters are needed.\n        """
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

    def override_dependencies(
        self, original: Callable[..., Any], override: Callable[..., Any]
    ) -> None:
        """Override a dependency with a new one.\n\n        Example:\n            \n            from aioclock import AioClock\n\n            def original_dependency():\n                return 1\n\n            def new_dependency():\n                return 2\n\n            app = AioClock()\n            app.override_dependencies(original=original_dependency, override=new_dependency)\n            \n        """
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        """Include a group of tasks that will be run by AioClock.\n\n        Example:\n            \n            from aioclock import AioClock, Group, Once\n\n            app = AioClock()\n\n            group = Group()\n            @group.task(trigger=Once())\n            async def main():\n                print("Hello World")\n\n            app.include_group(group)\n            \n        """
        self._groups.append(group)
        return None

    def task(self, *, trigger: BaseTrigger):
        """Decorator to add a task to the AioClock instance.\n\n        Example:\n            \n            from aioclock import AioClock, Once\n\n            app = AioClock()\n\n            @app.task(trigger=Once())\n            async def main():\n                print("Hello World")\n            \n        """

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                """Synchronous wrapper to ensure threading support."""
                asyncio.run(func(*args, **kwargs))

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
        """\n        Serves AioClock.\n        Run the tasks in the right order.\n        First, run the startup tasks, then run the tasks, and finally run the shutdown tasks.\n        """

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