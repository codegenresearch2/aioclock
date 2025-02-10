import asyncio
import threading
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp
from typing import Annotated

# service1.py
group = Group()


def dependency():
    return f"Hello, world! on thread: {threading.current_thread().ident}"


@group.task(trigger=Every(seconds=2))
async def async_task(val: str = Depends(dependency)):
    print(f"Async task is running with value: {val}")


@group.task(trigger=Every(seconds=2.01))
def sync_task_1(val: Annotated[str, Depends(dependency)]):
    print(f"Sync task 1 is running with value: {val}")


@group.task(trigger=Every(seconds=2.02))
def sync_task_2(val: Annotated[str, Depends(dependency)]):
    result = val  # Simulating a return value
    print(f"Sync task 2 is running with value: {val}")
    return result


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup(val: Annotated[str, Depends(dependency)]):
    print(f"Startup: {val}")


@app.task(trigger=OnShutDown())
def shutdown(val: Annotated[str, Depends(dependency)]):
    print(f"Shutdown: {val}")


if __name__ == "__main__":
    asyncio.run(app.serve())