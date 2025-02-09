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

from aioclock.provider import get_provider
from aioclock.task import Task
from aioclock.triggers import BaseTrigger

T = TypeVar("T")
P = ParamSpec("P")


class Group:
    def __init__(self, *, limiter=None):
        """
        Group of tasks that will be run together.

        Best use case is to have a good modularity and separation of concerns.
        For example, you can have a group of tasks that are responsible for sending emails.
        And another group of tasks that are responsible for sending notifications.

        :param limiter: Optional capacity limiter for the group tasks.
        :type limiter: Optional[anyio.CapacityLimiter]
        """
        self._tasks = []
        self.limiter = limiter

    def task(self, *, trigger: BaseTrigger):
        """
        Function used to decorate tasks, to be registered inside AioClock.

        :param trigger: The trigger that determines when the task should run.
        :type trigger: BaseTrigger
        :return: The decorated function.
        :rtype: Callable[P, Awaitable[T]]
        """

        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            async def wrapped_function(*args: P.args, **kwargs: P.kwargs) -> T:
                if asyncify(func) is not func:
                    return await func(*args, **kwargs)
                else:
                    return await asyncio.to_thread(func, *args, **kwargs)

            self._tasks.append(
                Task(
                    func=inject(wrapped_function, dependency_overrides_provider=get_provider()),
                    trigger=trigger,
                )
            )
            return wrapped_function

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
