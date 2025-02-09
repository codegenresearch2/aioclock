import asyncio
import threading
from aioclock import AioClock, Depends, Every, Group, Annotated
from typing import Callable

# service1.py
group = Group()


def dependency() -> str:
    return "Hello, world!"


@group.task(trigger=Every(seconds=2))
def sync_task_1(val: str = Depends(dependency)) -> None:
    print(f"Sync task is running on thread {threading.current_thread().ident}. {val}")
    # Simulate blocking operation
    time.sleep(1)


@group.task(trigger=Every(seconds=2))
def async_task_2(val: str = Depends(dependency)) -> None:
    print(f"Async task is running on thread {threading.current_thread().ident}. {val}")
    asyncio.sleep(1)


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup(val: str = Depends(dependency)) -> None:
    print(f"Starting up... {val}")


@app.task(trigger=OnShutDown())
def shutdown(val: str = Depends(dependency)) -> None:
    print(f"Shutting down... {val}")


if __name__ == "__main__":
    asyncio.run(app.serve())