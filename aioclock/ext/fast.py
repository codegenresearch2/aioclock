"""FastAPI extension to manage the tasks of the AioClock instance in HTTP Layer.\n\nUse cases:\n    - Expose the tasks of the AioClock instance in an HTTP API.\n    - Show to your client which task is going to be run next, and at which time.\n    - Run a specific task from an HTTP API immediately if needed.\n\nTo use FastAPI Extension, please make sure you do `pip install aioclock[fastapi]`."""

from typing import Union
from uuid import UUID

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
    """Make a FastAPI router that exposes the tasks of the AioClock instance and its external python API in HTTP Layer.\n    You can pass a router to this function, and have dependencies injected in the router, or any authorization logic that you want to have.\n\n    Parameters:\n        aioclock (AioClock): The AioClock instance to interact with.\n        router (Union[APIRouter, None]): An optional FastAPI router to include the endpoints.\n\n    Examples:\n        Example 1:\n            import asyncio\n            from contextlib import asynccontextmanager\n\n            from fastapi import FastAPI\n\n            from aioclock import AioClock\n            from aioclock.ext.fast import make_fastapi_router\n            from aioclock.triggers import Every, OnStartUp\n\n            clock_app = AioClock()\n\n            @clock_app.task(trigger=OnStartUp())\n            async def startup():\n                print("Starting...")\n\n            @clock_app.task(trigger=Every(seconds=3600))\n            async def foo():\n                print("Foo is processing...")\n\n            @asynccontextmanager\n            async def lifespan(app: FastAPI):\n                task = asyncio.create_task(clock_app.serve())\n                yield\n\n                try:\n                    task.cancel()\n                    await task\n                except asyncio.CancelledError:\n                    ...\n\n            app = FastAPI(lifespan=lifespan)\n            app.include_router(make_fastapi_router(clock_app))\n\n            if __name__ == "__main__":\n                import uvicorn\n                # uvicorn.run(app)\n    """
    router = router or APIRouter()

    @router.get("/tasks")
    async def get_tasks() -> list[TaskMetadata]:
        return await get_metadata_of_all_tasks(aioclock)

    @router.post("/task/{task_id}")
    async def run_task(task_id: UUID):
        try:
            await run_specific_task(task_id, aioclock)
        except TaskIdNotFound:
            raise HTTPException(status_code=404, detail="Task not found")

    return router