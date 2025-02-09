from aioclock import AioClock, Once
from aioclock.api import run_specific_task, get_metadata_of_all_tasks
from typing import List, Optional
from uuid import UUID
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import JSONResponse

app = AioClock()

@app.task(trigger=Once())
def main():
    """
    This function prints 'Hello World' and returns a value.
    """
    print('Hello World')

class TaskMetadata:
    def __init__(self, id: UUID, trigger, task_name: str):
        self.id = id
        self.trigger = trigger
        self.task_name = task_name

async def get_task_metadata(task_id: UUID, app: AioClock) -> Optional[TaskMetadata]:
    tasks = await get_metadata_of_all_tasks(app)
    for task in tasks:
        if task.id == task_id:
            return TaskMetadata(id=task.id, trigger=task.trigger, task_name=task.task_name)
    return None

async def run_task(task_id: UUID, app: AioClock):
    try:
        await run_specific_task(task_id, app)
    except TaskIdNotFound:
        raise HTTPException(status_code=404, detail='Task not found')

def create_fastapi_app() -> FastAPI:
    router = APIRouter()

    @router.get('/tasks/{task_id}')
    async def get_task(task_id: UUID):
        task_metadata = await get_task_metadata(task_id, app)
        if task_metadata:
            return task_metadata
        else:
            raise HTTPException(status_code=404, detail='Task not found')

    @router.post('/tasks/{task_id}/run')
    async def run_task_endpoint(task_id: UUID):
        await run_task(task_id, app)
        return JSONResponse(content={'status': 'Task is running'})

    fastapi_app = FastAPI()
    fastapi_app.include_router(router)
    return fastapi_app

# Example usage
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(create_fastapi_app(), host='0.0.0.0', port=8000)