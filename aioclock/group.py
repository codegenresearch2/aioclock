import asyncio
import sys
from functools import wraps
from typing import Awaitable, Callable, TypeVar, Union, Optional

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject
from asyncer import asyncify
import anyio

from aioclock.provider import get_provider
from aioclock.task import Task
from aioclock.triggers import BaseTrigger

T = TypeVar("T")
P = ParamSpec("P")


class Group:
    def __init__(self, *, tasks: Union[list[Task], None] = None, limiter: Optional[anyio.CapacityLimiter] = None):
        """
        Group of tasks that will be run together.

        Best use case is to have a good modularity and separation of concerns.
        For example, you can have a group of tasks that are responsible for sending emails.
        And another group of tasks that are responsible for sending notifications.

        Args:
            tasks (Union[list[Task], None]): Optional list of tasks to initialize the group with.
            limiter (Optional[anyio.CapacityLimiter]): Optional limiter to limit the number of concurrent tasks.
        """
        self._tasks: list[Task] = tasks or []
        self._limiter = limiter

    def task(self, *, trigger: BaseTrigger):
        """Function used to decorate tasks, to be registered inside AioClock.

        Args:
            trigger (BaseTrigger): The trigger that will be used to run the task.

        Returns:
            Callable[[Callable[P, Union[Awaitable[T], T]]], Callable[P, Union[Awaitable[T], T]]]: The decorated function.
        """

        def decorator(func: Callable[P, Union[Awaitable[T], T]]) -> Callable[P, Union[Awaitable[T], T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = asyncify(func)(*args, **kwargs)
                return result

            task = Task(
                func=inject(wrapper, dependency_overrides_provider=get_provider()),
                trigger=trigger,
            )
            self._tasks.append(task)
            return wrapper

        return decorator

    async def _run(self):
        """
        Just for purpose of being able to run all task in group
        Private method, should not be used outside of the library
        """
        if self._limiter:
            async with self._limiter:
                await asyncio.gather(
                    *(task.run() for task in self._tasks),
                    return_exceptions=False,
                )
        else:
            await asyncio.gather(
                *(task.run() for task in self._tasks),
                return_exceptions=False,
            )