import sys
from typing import Any, Awaitable, Callable, TypeVar, Union
from uuid import UUID

from fast_depends import inject
from pydantic import BaseModel

from aioclock.app import AioClock
from aioclock.exceptions import TaskIdNotFound
from aioclock.provider import get_provider
from aioclock.triggers import TriggerT

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

T = TypeVar('T')
P = ParamSpec('P')


class TaskMetadata(BaseModel):
    """Metadata of the task that is included in the AioClock instance.

    Attributes:
        id (UUID): Task ID that is unique for each task, and changes every time you run the aioclock app. In future, we might store task ID in a database, so that it always remains same.
        trigger (Union[TriggerT, Any]): Trigger that is used to run the task, type is also any to ease implementing new triggers.
        task_name (str): Name of the task function.
    """
    id: UUID
    trigger: Union[TriggerT, Any]
    task_name: str


async def run_specific_task(task_id: UUID, app: AioClock):
    """Run a specific task immediately by its ID, from the AioClock instance.

    Args:
        task_id (UUID): The ID of the task to run.
        app (AioClock): The AioClock instance to run the task on.

    Raises:
        TaskIdNotFound: If the task with the given ID is not found in the AioClock instance.

    Returns:
        The result of running the task with injected dependencies.
    """
    task = next((task for task in app._tasks if task.id == task_id), None)
    if not task:
        raise TaskIdNotFound
    return await run_with_injected_deps(task.func)


async def run_with_injected_deps(func: Callable[P, Awaitable[T]]) -> T:
    """Runs an aioclock decorated function, with all the dependencies injected.

    Args:
        func (Callable[P, Awaitable[T]]): The function to run with dependencies injected.

    Returns:
        The result of the function with dependencies injected.
    """
    return await inject(func, dependency_overrides_provider=get_provider())()  # type: ignore


async def get_metadata_of_all_tasks(app: AioClock) -> list[TaskMetadata]:
    """Get metadata of all tasks that are included in the AioClock instance.

    Args:
        app (AioClock): The AioClock instance to get tasks from.

    Returns:
        A list of TaskMetadata objects containing metadata of all tasks.
    """
    return [
        TaskMetadata(
            id=task.id,
            trigger=task.trigger,
            task_name=task.func.__name__,
        )
        for task in app._get_tasks(exclude_type=set())
    ]