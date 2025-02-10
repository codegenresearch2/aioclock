import asyncio
import threading
import time

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency():
    return "Hello, world!"


@group.task(trigger=Every(seconds=2))
async def task_every_two_seconds(val: str = Depends(dependency)):
    print(f"Every 2 seconds task executed by thread {threading.current_thread().ident}: {val}")


@group.task(trigger=Every(seconds=5))
async def task_every_five_seconds(val: str = Depends(dependency)):
    print(f"Every 5 seconds task executed by thread {threading.current_thread().ident}: {val}")


# Introduce synchronous tasks with blocking operations
def blocking_dependency():
    time.sleep(1)
    return "Blocked dependency"


@group.task(trigger=OnStartUp())
def startup(val: str = Depends(blocking_dependency)):
    print(f"Startup executed by thread {threading.current_thread().ident}: {val}")


@group.task(trigger=OnShutDown())
def shutdown(val: str = Depends(dependency)):
    print(f"Shutdown executed by thread {threading.current_thread().ident}: {val}")


# app.py
app = AioClock()
app.include_group(group)


if __name__ == "__main__":
    asyncio.run(app.serve())