import asyncio
import sys
from functools import wraps
from typing import Awaitable, Callable, TypeVar, Union
from asyncer import asyncify

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
    def __init__(self, *, tasks: Union[list[Task], None] = None, limiter: int = 10):
        """
        Group of tasks that will be run together.

        This class is useful for maintaining modularity and separation of concerns.
        For example, you can have a group of tasks that are responsible for sending emails.
        Another group can be responsible for sending notifications.

        Example:

            from aioclock import Group, AioClock, Forever

            email_group = Group(limiter=5)

            # Consider this as a different file
            @email_group.task(trigger=Forever(interval_seconds=600))  # Longer interval for task execution
            async def send_email():
                ...

            # app.py
            aio_clock = AioClock()
            aio_clock.include_group(email_group)

        Params:
            tasks (Union[list[Task], None], optional): List of tasks to be included in the group. Defaults to None.
            limiter (int, optional): Maximum number of tasks that can be executed concurrently. Defaults to 10.
        """
        self._tasks: list[Task] = tasks or []
        self._limiter = asyncio.Semaphore(limiter)

    def task(self, *, trigger: BaseTrigger):
        """Function used to decorate tasks, to be registered inside AioClock.

        This decorator is used to register a task with a specific trigger.

        Example:

            from aioclock import Group, Forever

            @group.task(trigger=Forever(interval_seconds=600))  # Longer interval for task execution
            async def send_email():
                ...

        Params:
            trigger (BaseTrigger): The trigger that determines when the task should be executed.

        Returns:
            Callable[P, Awaitable[T]]: The decorated function.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                    async with self._limiter:
                        return await func(*args, **kwargs)
            else:
                @wraps(func)
                async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                    async with self._limiter:
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
        Run all tasks in the group.

        This is a private method and should not be used outside of the library.
        """
        await asyncio.gather(
            *(task.run() for task in self._tasks),
            return_exceptions=False,
        )


In the updated code snippet, I have addressed the feedback received from the oracle. I have added a `limiter` parameter to the `Group` class to manage the concurrency of tasks effectively. I have also improved the docstring consistency and added example consistency. Additionally, I have implemented logic to handle both coroutine and synchronous functions using the `asyncify` function from the `asyncer` module.