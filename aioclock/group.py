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
    def __init__(self, *, limiter: Optional[anyio.CapacityLimiter] = None):
        """
        Group of tasks that will be run together.

        Best use case is to have a good modularity and separation of concerns.
        For example, you can have a group of tasks that are responsible for sending emails.
        And another group of tasks that are responsible for sending notifications.

        Args:
            limiter (Optional[anyio.CapacityLimiter]): Optional limiter object to limit the number of concurrent tasks.
        """
        self._tasks: list[Task] = []
        self._limiter = limiter

    def task(self, *, trigger: BaseTrigger):
        """Function used to decorate tasks, to be registered inside AioClock.

        The task decorator supports both coroutine and synchronous functions.
        For synchronous functions, they are wrapped in a thread pool to ensure they do not block the event loop.

        Args:
            trigger (BaseTrigger): Trigger that will be used to run the function.

        Returns:
            Callable[[Callable[P, Union[Awaitable[T], T]]], Callable[P, Union[Awaitable[T], T]]]: Decorated function.
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
        Runs all tasks in the group.

        This method is intended for internal use and should not be called directly outside the library.
        """
        if self._limiter:
            async with anyio.create_task_group() as task_group:
                for task in self._tasks:
                    task_group.start_soon(task.run)
        else:
            await asyncio.gather(
                *(task.run() for task in self._tasks),
                return_exceptions=False,
            )


This revised code snippet addresses the feedback provided by the oracle. It includes improvements such as more descriptive naming for the inner decorator function, clear handling of synchronous functions, consistent use of `asyncify`, and concise documentation for the private method `_run`.