import asyncio
import threading
from typing import Union
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from aioclock.api import TaskMetadata, get_metadata_of_all_tasks, run_specific_task
from aioclock.app import AioClock
from aioclock.exceptions import TaskIdNotFound

try:
    from fastapi.exceptions import HTTPException
    from fastapi.routing import APIRouter
except ImportError:
    raise ImportError(
        "You need to install fastapi to use aioclock with FastAPI. Please run `pip install aioclock[fastapi]`"
    )

# Define a thread pool executor for synchronous tasks
thread_pool = ThreadPoolExecutor(max_workers=10)

def make_fastapi_router(aioclock: AioClock, router: Union[APIRouter, None] = None):
    """Make a FastAPI router that exposes the tasks of the AioClock instance and its external python API in HTTP Layer.
    This function supports synchronous tasks with threading and implements capacity limiting for task execution.

    Example:
        
        import asyncio
        from contextlib import asynccontextmanager

        from fastapi import FastAPI

        from aioclock import AioClock
        from aioclock.ext.fast import make_fastapi_router
        from aioclock.triggers import Every, OnStartUp

        clock_app = AioClock()

        @clock_app.task(trigger=OnStartUp())
        def startup():
            print("Starting...")

        @clock_app.task(trigger=Every(seconds=3600))
        def foo():
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
        app.include_router(make_fastapi_router(clock_app))

        if __name__ == "__main__":
            import uvicorn
            # uvicorn.run(app)
        
    """
    router = router or APIRouter()

    @router.get("/tasks")
    async def get_tasks() -> list[TaskMetadata]:
        """
        Get metadata of all tasks that are included in the AioClock instance.

        Returns:
            list[TaskMetadata]: List of task metadata objects.
        """
        return await get_metadata_of_all_tasks(aioclock)

    @router.post("/task/{task_id}")
    async def run_task(task_id: UUID):
        """
        Run a specific task immediately by its ID, from the AioClock instance.

        Args:
            task_id (UUID): Task ID that is unique for each task.

        Raises:
            HTTPException: If the task ID is not found.
        """
        try:
            task = next((task for task in aioclock._tasks if task.id == task_id), None)
            if not task:
                raise TaskIdNotFound

            # Check if the task is synchronous and run it in a thread pool
            if asyncio.iscoroutinefunction(task.func):
                await run_specific_task(task_id, aioclock)
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(thread_pool, task.func)
        except TaskIdNotFound:
            raise HTTPException(status_code=404, detail="Task not found")

    return router