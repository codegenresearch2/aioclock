import asyncio
import threading
import time
from typing import Annotated

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency():
    return "Thread context: " + threading.current_thread().name


@group.task(trigger=Every(seconds=2.01))
async def async_task(val: str = Depends(dependency)):
    print(f"Async task executed by thread {threading.current_thread().ident}: {val}")


# Introduce synchronous tasks with blocking operations
def blocking_dependency():
    time.sleep(1)
    return "Blocked dependency"


@group.task(trigger=Every(seconds=3))
def sync_task_1(val: str = Depends(blocking_dependency)):
    print(f"Sync task 1 executed by thread {threading.current_thread().ident}: {val}")
    return "Sync task 1 completed"


@group.task(trigger=Every(seconds=3))
def sync_task_2(val: str = Depends(dependency)):
    print(f"Sync task 2 executed by thread {threading.current_thread().ident}: {val}")
    return "Sync task 2 completed"


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup(val: str = Depends(dependency)):
    print(f"Startup executed by thread {threading.current_thread().ident}: {val}")
    return "Startup completed"


@app.task(trigger=OnShutDown())
def shutdown(val: str = Depends(dependency)):
    print(f"Shutdown executed by thread {threading.current_thread().ident}: {val}")
    return "Shutdown completed"


if __name__ == "__main__":
    asyncio.run(app.serve())