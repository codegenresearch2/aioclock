import asyncio
import sys
from functools import wraps
from typing import Awaitable, Callable, TypeVar, Union

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
    def __init__(self):
        """
        Group of tasks that will be run together.
        """
        self._tasks = []

    def task(self, *, trigger: BaseTrigger):
        """Function used to decorate tasks, to be registered inside AioClock."""

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await asyncify(func)(*args, **kwargs)

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
        Just for purpose of being able to run all task in group
        Private method, should not be used outside of the library
        """
        await asyncio.gather(
            *(task.run() for task in self._tasks),
            return_exceptions=False,
        )
