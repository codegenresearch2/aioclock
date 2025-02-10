import sys
from typing import Any, Awaitable, Callable, TypeVar, Union
from uuid import UUID
from asyncio import Semaphore

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

T = TypeVar("T")
P = ParamSpec("P")

# Capacity limiter for tasks
TASK_SEMAPHORE = Semaphore(10)

class TaskMetadata(BaseModel):
    """
    Metadata of the task that is included in the AioClock instance.

    Attributes:
        id (UUID): Task ID that is unique for each task. Changes every time the aioclock app is run.
            In the future, task IDs may be stored in a database to persist across runs.
        trigger (Union[TriggerT, Any]): Trigger that is used to run the task. Type is any to accommodate custom triggers.
        task_name (str): Name of the task function.
    """

    id: UUID
    trigger: Union[TriggerT, Any]
    task_name: str

async def run_specific_task(task_id: UUID, app: AioClock):
    """
    Run a specific task immediately by its ID, from the AioClock instance.

    Args:
        task_id (UUID): The ID of the task to run.
        app (AioClock): The AioClock instance containing the task.

    Raises:
        TaskIdNotFound: If the task ID is not found in the AioClock instance.

    Returns:
        The result of the task function.

    Example:
        
        from aioclock import AioClock, Once
        from aioclock.api import run_specific_task

        app = AioClock()

        @app.task(trigger=Once())
        async def main():
            print("Hello World")

        async def some_other_func():
            await run_specific_task(app._tasks[0].id, app)
        

    Note:
        Changes made to the AioClock instance's state are not persisted, as the state is currently stored in memory.
    """

    async with TASK_SEMAPHORE:
        task = next((task for task in app._tasks if task.id == task_id), None)
        if not task:
            raise TaskIdNotFound
        return await run_with_injected_deps(task.func)

async def run_with_injected_deps(func: Callable[P, Awaitable[T]]) -> T:
    """
    Runs an aioclock decorated function, with all the dependencies injected.

    Args:
        func (Callable[P, Awaitable[T]]): The function to run with injected dependencies.

    Returns:
        The result of the function.

    Example:
        
        from aioclock import Once, AioClock, Depends
        from aioclock.api import run_with_injected_deps

        app = AioClock()

        def some_dependency():
            return 1

        @app.task(trigger=Once())
        async def main(bar: int = Depends(some_dependency)):
            print("Hello World")
            return bar

        async def some_other_func():
            foo = await run_with_injected_deps(main)
            assert foo == 1
        

    Note:
        Changes made to the AioClock instance's state are not persisted, as the state is currently stored in memory.
    """

    async with TASK_SEMAPHORE:
        return await inject(func, dependency_overrides_provider=get_provider())()  # type: ignore

async def get_metadata_of_all_tasks(app: AioClock) -> list[TaskMetadata]:
    """
    Get metadata of all tasks that are included in the AioClock instance.

    Args:
        app (AioClock): The AioClock instance containing the tasks.

    Returns:
        A list of TaskMetadata objects for all tasks in the AioClock instance.

    Example:
        
        from aioclock import AioClock, Once
        from aioclock.api import get_metadata_of_all_tasks

        app = AioClock()
        @app.task(trigger=Once())
        async def main(): ...

        async def some_other_func():
            metadata = await get_metadata_of_all_tasks(app)
        
    """

    return [
        TaskMetadata(
            id=task.id,
            trigger=task.trigger,
            task_name=task.func.__name__,
        )
        for task in app._get_tasks(exclude_type=set())
    ]