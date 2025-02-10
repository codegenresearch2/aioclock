import asyncio
import sys
from functools import wraps
from typing import Awaitable, Callable, Optional, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject

from aioclock.provider import get_provider
from aioclock.task import Task
from aioclock.triggers import BaseTrigger

T = TypeVar("T")
P = ParamSpec("P")

class Group:
    def __init__(self, tasks: Optional[list[Task]] = None):
        """
        Group of tasks that will be run together.

        This class is used to group tasks that are related to each other.
        It provides a way to manage and run these tasks together.

        Args:
            tasks (Optional[list[Task]]): A list of tasks to be included in the group.
                If not provided, an empty list is used.
        """
        self._tasks: list[Task] = tasks or []

    def task(self, trigger: BaseTrigger):
        """Function used to decorate tasks, to be registered inside AioClock.

        This decorator is used to register a task with a specific trigger.
        The decorated function will be run according to the trigger's schedule.

        Args:
            trigger (BaseTrigger): The trigger that determines when the task should be run.

        Returns:
            Callable[P, Awaitable[T]]: The decorated function.
        """
        def decorator(func: Callable[P, Union[Awaitable[T], T]]) -> Callable[P, Union[Awaitable[T], T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            self._tasks.append(
                Task(
                    func=inject(wrapper, dependency_overrides_provider=get_provider()),
                    trigger=trigger,
                )
            )
            return wrapper

        return decorator

    async def _run(self):
        """
        Run all tasks in the group.

        This method is used to run all tasks in the group concurrently.
        It should not be used outside of the library.
        """
        await asyncio.gather(
            *(task.run() for task in self._tasks),
            return_exceptions=False,
        )