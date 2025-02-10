import sys
import threading
from functools import wraps
from typing import Callable, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject
from anyio import create_task_group, run

from aioclock.provider import get_provider
from aioclock.task import Task
from aioclock.triggers import BaseTrigger

T = TypeVar("T")
P = ParamSpec("P")

class Group:
    def __init__(self, *, tasks: Union[list[Task], None] = None):
        """
        Group of tasks that will be run together.
        This group supports synchronous tasks with threading.

        Example:
            
            from aioclock import Group, AioClock, Forever

            email_group = Group()

            # consider this as different file
            @email_group.task(trigger=Forever())
            def send_email():
                ...

            # app.py
            aio_clock = AioClock()
            aio_clock.include_group(email_group)
            
        """
        self._tasks: list[Task] = tasks or []

    def task(self, *, trigger: BaseTrigger):
        """Function used to decorate tasks, to be registered inside AioClock.
        This decorator supports synchronous tasks with threading.

        Example:
            
            from aioclock import Group, Forever
            @group.task(trigger=Forever())
            def send_email():
                ...
            
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
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
        Just for purpose of being able to run all tasks in group.
        This method uses AnyIO for better concurrency management.
        Private method, should not be used outside of the library.
        """
        async with create_task_group() as tg:
            for task in self._tasks:
                tg.start_soon(self._run_task, task)

    async def _run_task(self, task: Task):
        """
        Helper method to run a single task.
        This method supports synchronous tasks with threading.
        """
        while task.trigger.should_trigger():
            try:
                next_trigger = await task.trigger.get_waiting_time_till_next_trigger()
                if next_trigger is not None:
                    print(f"Triggering next task {task.func.__name__} in {next_trigger} seconds")
                    task.trigger.expected_trigger_time = datetime.now(UTC) + timedelta(seconds=next_trigger)
                await task.trigger.trigger_next()
                print(f"Running task {task.func.__name__}")
                if asyncio.iscoroutinefunction(task.func):
                    await task.func()
                else:
                    await run(self._run_sync_task, task.func)
            except Exception as error:
                print(f"Error running task {task.func.__name__}: {error}")

        task.trigger.expected_trigger_time = None

    async def _run_sync_task(self, func: Callable):
        """
        Helper method to run a synchronous task in a separate thread.
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, func)
        return result