import asyncio
import threading
from time import sleep
from typing import Annotated

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()

def dependency():
    return "Hello, world!"

def sync_dependency():
    sleep(1)
    return dependency()

@group.task(trigger=Every(seconds=2), metadata={'mutable': False})
def sync_task_1(val: Annotated[str, Depends(sync_dependency)]):
    print(f"Synchronous task 1 running in thread {threading.current_thread().ident}: {val}")

@group.task(trigger=Every(seconds=2.01), metadata={'mutable': False})
def sync_task_2(val: Annotated[str, Depends(sync_dependency)]):
    sleep(1)
    print(f"Synchronous task 2 running in thread {threading.current_thread().ident}: {val}")

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp(), metadata={'mutable': False})
def startup():
    print("Startup task running: Welcome!")

@app.task(trigger=OnShutDown(), metadata={'mutable': False})
def shutdown():
    print("Shutdown task running: Bye!")

@app.task(trigger=Every(seconds=1), metadata={'mutable': False})
async def async_task(val: Annotated[str, Depends(sync_dependency)]):
    print(f"Asynchronous task running in thread {threading.current_thread().ident}: {val}")

if __name__ == "__main__":
    asyncio.run(app.serve())