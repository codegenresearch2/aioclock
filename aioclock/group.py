import asyncio
import sys
from functools import wraps
from typing import Awaitable, Callable, Optional, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject
from asyncer import asyncify
from anyio import CapacityLimiter

from aioclock.provider import get_provider
from aioclock.task import Task
from aioclock.triggers import BaseTrigger

T = TypeVar("T")
P = ParamSpec("P")


class Group:
    def __init__(self, *, limiter: Optional[CapacityLimiter] = None):
        """
        A group of tasks that will be run together.

        Args:
            limiter (Optional[CapacityLimiter], optional): A limiter to limit the number of concurrent tasks.
        """
        self._tasks: list[Task] = []
        self._limiter = limiter

    def task(self, *, trigger: BaseTrigger):
        """Decorate a function to register it as a task in the group.

        Args:
            trigger (BaseTrigger): The trigger that determines when the task should run.

        Returns:
            Callable[[Callable[P, Union[Awaitable[T], T]]], Callable[P, Union[Awaitable[T], T]]]: The decorated function.
        """

        def decorator(func: Callable[P, Union[Awaitable[T], T]]) -> Callable[P, Union[Awaitable[T], T]]:
            @wraps(func)
            async def wrapped_function(*args: P.args, **kwargs: P.kwargs) -> Union[Awaitable[T], T]:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return asyncify(func)(*args, **kwargs)

            task = Task(
                func=inject(wrapped_function, dependency_overrides_provider=get_provider()),
                trigger=trigger,
            )
            self._tasks.append(task)
            return wrapped_function

        return decorator

    async def _run(self):
        """
        Run all tasks in the group.

        This method is intended for internal use and should not be called directly.
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