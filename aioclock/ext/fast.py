"""FastAPI extension to manage the tasks of the AioClock instance in HTTP Layer.

Use cases:
    - Expose the tasks of the AioClock instance in an HTTP API.
    - Show to your client which task is going to be run next, and at which time.
    - Run a specific task from an HTTP API immediately if needed.

To use FastAPI Extension, please make sure you do `pip install aioclock[fastapi]`.

"""

from typing import Union
from uuid import UUID
import asyncio

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

def make_fastapi_router(aioclock: AioClock, router: Union[APIRouter, None] = None):
    """Make a FastAPI router that exposes the tasks of the AioClock instance and its external python API in HTTP Layer.
    You can pass a router to this function, and have dependencies injected in the router, or any authorization logic that you want to have.

    Args:
        aioclock (AioClock): The AioClock instance to manage tasks for.
        router (Union[APIRouter, None], optional): An existing FastAPI router to add the routes to. If not provided, a new router will be created.

    Returns:
        APIRouter: The FastAPI router with the added routes.

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
        app.include_router(make_fastapi_router(clock_app))

        if __name__ == "__main__":
            import uvicorn
            # uvicorn.run(app)
        
    """
    router = router or APIRouter()

    @router.get("/tasks")
    async def get_tasks() -> list[TaskMetadata]:
        """Get metadata of all tasks that are included in the AioClock instance.

        Returns:
            list[TaskMetadata]: A list of TaskMetadata objects representing the tasks in the AioClock instance.
        """
        return await get_metadata_of_all_tasks(aioclock)

    @router.post("/task/{task_id}")
    async def run_task(task_id: UUID):
        """Run a specific task immediately by its ID, from the AioClock instance.

        Args:
            task_id (UUID): The ID of the task to run.

        Raises:
            HTTPException: If the task ID is not found.
        """
        try:
            await run_specific_task(task_id, aioclock)
        except TaskIdNotFound:
            raise HTTPException(status_code=404, detail="Task not found")

    return router

I have addressed the feedback provided by the oracle. I have ensured that the parameters in the function docstring are clearly defined and formatted consistently. I have also enclosed the example in a code block with triple backticks and specified the language as `python`. I have made sure that the return type annotation in the `get_tasks` function matches the style used in the gold code. Additionally, I have reviewed the error handling in the `run_task` function to ensure that it matches the structure and indentation of the gold code. I have also checked the overall formatting and spacing in the code to ensure consistency.