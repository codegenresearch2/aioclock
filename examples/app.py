import asyncio
import threading
import time
from typing import Annotated

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency() -> str:
    return f'Hello, world! (Thread ID: {threading.current_thread().ident}')  # Updated dependency function to include thread ID

@group.task(trigger=Every(seconds=2))
async def my_async_task(val: Annotated[str, Depends(dependency)]) -> None:
    print(f'Async Task value: {val} (Thread ID: {threading.current_thread().ident})')

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
sync_task_1 = group.sync_task(trigger=OnStartUp())
def startup(val: Annotated[str, Depends(dependency)]) -> str:
    print(f'Startup Task (Thread ID: {threading.current_thread().ident})')
    time.sleep(1)  # Simulate blocking operation
    return val

@app.task(trigger=OnShutDown())
sync_task_2 = group.sync_task(trigger=OnShutDown())
def shutdown(val: Annotated[str, Depends(dependency)]) -> str:
    print(f'Shutdown Task (Thread ID: {threading.current_thread().ident})')
    time.sleep(1)  # Simulate blocking operation
    return val

if __name__ == '__main__':
    asyncio.run(app.serve())