import asyncio
import threading
from time import sleep
from typing import Annotated

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()

def dependency():
    return f"Hello, world! from thread {threading.current_thread().ident}"

def sync_dependency():
    sleep(1)
    return dependency()

@group.task(trigger=Every(seconds=2))
def sync_task_1(val: str = Depends(sync_dependency)):
    print(f"Sync task 1 running: {val}")
    sleep(1)

@group.task(trigger=Every(seconds=2.01))
def sync_task_2(val: Annotated[str, Depends(sync_dependency)]):
    print(f"Sync task 2 running: {val}")
    sleep(1)
    return "Sync task 2 completed"

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
def startup(val: str = Depends(dependency)):
    print(f"Startup task running: Welcome! {val}")

@app.task(trigger=OnShutDown())
def shutdown(val: str = Depends(dependency)):
    print(f"Shutdown task running: Bye! {val}")

@app.task(trigger=Every(seconds=1))
async def async_task(val: str = Depends(sync_dependency)):
    print(f"Async task running: {val}")

if __name__ == "__main__":
    asyncio.run(app.serve())