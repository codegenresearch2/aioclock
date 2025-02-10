import asyncio
import sys
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, Union

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

from fast_depends import inject
from async_tools import asyncify

from aioclock.custom_types import Triggers
from aioclock.group import Group, Task
from aioclock.provider import get_provider
from aioclock.triggers import BaseTrigger
from aioclock.utils import flatten_chain

T = TypeVar("T")
P = ParamSpec("P")

class AioClock:
    def __init__(self, capacity_limit: int = None):
        self._groups: list[Group] = []
        self._app_tasks: list[Task] = []
        self.capacity_limit = capacity_limit

    _groups: list[Group]
    _app_tasks: list[Task]
    capacity_limit: int

    @property
    def dependencies(self):
        return get_provider()

    def override_dependencies(self, original: Callable[..., Any], override: Callable[..., Any]) -> None:
        self.dependencies.override(original, override)

    def include_group(self, group: Group) -> None:
        self._groups.append(group)

    def task(self, *, trigger: BaseTrigger):
        def decorator(func: Callable[P, Union[Awaitable[T], T]]) -> Callable[P, Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return await asyncify(func)(*args, **kwargs)

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
        return flatten_chain([group._tasks for group in self._groups])

    def _get_shutdown_task(self) -> list[Task]:
        return [task for task in self._tasks if task.trigger.type_ == Triggers.ON_SHUT_DOWN]

    def _get_startup_task(self) -> list[Task]:
        return [task for task in self._tasks if task.trigger.type_ == Triggers.ON_START_UP]

    def _get_tasks(self, exclude_type: Union[set[Triggers], None] = None) -> list[Task]:
        exclude_type = exclude_type if exclude_type is not None else {Triggers.ON_START_UP, Triggers.ON_SHUT_DOWN}
        return [task for task in self._tasks if task.trigger.type_ not in exclude_type]

    async def serve(self) -> None:
        self.include_group(Group(tasks=self._app_tasks))
        try:
            await asyncio.gather(*(task.run() for task in self._get_startup_task()), return_exceptions=False)

            tasks = self._get_tasks()
            if self.capacity_limit:
                semaphore = asyncio.Semaphore(self.capacity_limit)
                tasks = [semaphore.acquire() for _ in tasks] + [task.run() for task in tasks]
            else:
                tasks = [task.run() for task in tasks]

            await asyncio.gather(*tasks, return_exceptions=False)
        finally:
            shutdown_tasks = self._get_shutdown_task()
            await asyncio.gather(*(task.run() for task in shutdown_tasks), return_exceptions=False)