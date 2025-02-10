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

@group.task(trigger=Every(seconds=2), metadata={'mutable': False})
def sync_task_1(val: Annotated[str, Depends(sync_dependency)] = "Default"):
    print(f"Synchronous task 1 running in thread {threading.current_thread().ident}: {val}")

@group.task(trigger=Every(seconds=2.01), metadata={'mutable': False})
def sync_task_2(val: Annotated[str, Depends(sync_dependency)] = "Default"):
    sleep(1)
    print(f"Synchronous task 2 running in thread {threading.current_thread().ident}: {val}")
    return "3"

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp(), metadata={'mutable': False})
def startup(val: Annotated[str, Depends(sync_dependency)]):
    print(f"Startup task running: Welcome! {val}")

@app.task(trigger=OnShutDown(), metadata={'mutable': False})
def shutdown(val: Annotated[str, Depends(sync_dependency)]):
    print(f"Shutdown task running: Bye! {val}")

@app.task(trigger=Every(seconds=1), metadata={'mutable': False})
async def async_task(val: Annotated[str, Depends(sync_dependency)]):
    print(f"Asynchronous task running in thread {threading.current_thread().ident}: {val}")

if __name__ == "__main__":
    asyncio.run(app.serve())