import asyncio
import sys
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor

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
    """\n    AioClock is the main class that will be used to run the tasks.\n    It will be responsible for running the tasks in the right order.\n    Now it supports synchronous tasks with threading.\n    """

    def __init__(self):
        """\n        Initialize AioClock instance.\n        No parameters are needed.\n        """
        self._groups: list[Group] = []
        self._app_tasks: list[Task] = []
        self._executor = ThreadPoolExecutor()

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
        """Override a dependency with a new one."""
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        """Include a group of tasks that will be run by AioClock."""
        self._groups.append(group)

    def task(self, *, trigger: BaseTrigger):
        """Decorator to add a task to the AioClock instance."""

        def decorator(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                return await asyncio.get_event_loop().run_in_executor(self._executor, func, *args, **kwargs)

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
        """\n        Serves AioClock\n        Run the tasks in the right order.\n        First, run the startup tasks, then run the tasks, and finally run the shutdown tasks.\n        Now it supports adjustable intervals.\n        """

        self.include_group(Group(tasks=self._app_tasks))
        try:
            await asyncio.gather(
                *(task.run() for task in self._get_startup_task()), return_exceptions=False
            )

            await asyncio.gather(
                *(group.run_with_adjustable_intervals() for group in self._get_tasks()), return_exceptions=False
            )
        finally:
            shutdown_tasks = self._get_shutdown_task()
            await asyncio.gather(*(task.run() for task in shutdown_tasks), return_exceptions=False)

# Added a method to run tasks with adjustable intervals
@dataclass
class Group:
    """Group of tasks that can be run together."""

    tasks: list[Task] = field(default_factory=list)

    async def run_with_adjustable_intervals(self):
        """Run tasks with adjustable intervals."""
        tasks_to_run = self.tasks.copy()
        while tasks_to_run:
            for task in tasks_to_run:
                if task.trigger.should_trigger():
                    next_trigger = await task.trigger.get_waiting_time_till_next_trigger()
                    if next_trigger is not None:
                        await asyncio.sleep(next_trigger)
                    await task.run()
                else:
                    tasks_to_run.remove(task)