"""FastAPI extension to manage the tasks of the AioClock instance in HTTP Layer.

Use cases:
    - Expose the tasks of the AioClock instance in an HTTP API.
    - Show to your client which task is going to be run next, and at which time.
    - Run a specific task from an HTTP API immediately if needed.

To use FastAPI Extension, please make sure you do `pip install aioclock[fastapi]`.

"""

from typing import Union, Callable, Awaitable, TypeVar
from uuid import UUID
from asyncio import Semaphore

from aioclock.api import TaskMetadata, get_metadata_of_all_tasks, run_specific_task, run_with_injected_deps
from aioclock.app import AioClock
from aioclock.exceptions import TaskIdNotFound

try:
    from fastapi.exceptions import HTTPException
    from fastapi.routing import APIRouter
except ImportError:
    raise ImportError(
        "You need to install fastapi to use aioclock with FastAPI. Please run `pip install aioclock[fastapi]`"
    )

T = TypeVar("T")

def make_fastapi_router(aioclock: AioClock, router: Union[APIRouter, None] = None, capacity: int = 10):
    """Make a FastAPI router that exposes the tasks of the AioClock instance and its external python API in HTTP Layer.
    You can pass a router to this function, and have dependencies injected in the router, or any authorization logic that you want to have.

    Attributes:
        aioclock: AioClock instance to interact with.
        router: Optional FastAPI router to use. If not provided, a new one will be created.
        capacity: Maximum number of tasks that can be run concurrently.

    Example:
        
        import asyncio
        from contextlib import asynccontextmanager

        from fastapi import FastAPI

        from aioclock import AioClock
        from aioclock.ext.fast import make_fastapi_router
        from aioclock.triggers import Every, OnStartUp

        clock_app = AioClock()

        @clock_app.task(trigger=OnStartUp())
        async def startup():
            print("Starting...")

        @clock_app.task(trigger=Every(seconds=3600))
        async def foo():
            print("Foo is processing...")

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            task = asyncio.create_task(clock_app.serve())
            yield

            try:
                task.cancel()
                await task
            except asyncio.CancelledError:
                ...

        app = FastAPI(lifespan=lifespan)
        app.include_router(make_fastapi_router(clock_app, capacity=20))

        if __name__ == "__main__":
            import uvicorn
            # uvicorn.run(app)
        
    """
    router = router or APIRouter()
    semaphore = Semaphore(capacity)

    @router.get("/tasks")
    async def get_tasks() -> list[TaskMetadata]:
        return await get_metadata_of_all_tasks(aioclock)

    @router.post("/task/{task_id}")
    async def run_task(task_id: UUID):
        async with semaphore:
            try:
                await run_specific_task(task_id, aioclock)
            except TaskIdNotFound:
                raise HTTPException(status_code=404, detail="Task not found")

    @router.post("/run/{task_name}")
    async def run_task_by_name(task_name: str):
        async with semaphore:
            task = next((task for task in aioclock._tasks if task.func.__name__ == task_name), None)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            await run_with_injected_deps(task.func)

    return router


In the rewritten code, I have added a capacity limiter using a semaphore to limit the number of tasks that can be run concurrently. I have also added a new endpoint to run a task by its name. I have also clarified the functionality and parameters of the task decorator and added attributes for better understanding.