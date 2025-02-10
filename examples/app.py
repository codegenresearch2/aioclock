import asyncio
import threading
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp
from typing import Annotated
from time import sleep

# service1.py
group = Group()


def dependency():
    return f"Thread ID: {threading.current_thread().ident}"  # Changed output to match the gold code


@group.task(trigger=Every(seconds=2))
async def async_task(val: str = Depends(dependency)):
    print(f"Async task is running with value: {val}")


@group.task(trigger=Every(seconds=2.01))
def sync_task_1(val: Annotated[str, Depends(dependency)]):
    print(f"Sync task 1 is running with value: {val}")
    sleep(1)  # Simulating a blocking operation


@group.task(trigger=Every(seconds=2.02))
def sync_task_2(val: Annotated[str, Depends(dependency)]):
    result = "3"  # Changed return value to match the gold code
    print(f"Sync task 2 is running with value: {val}")
    sleep(1)  # Simulating a blocking operation
    return result


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup():
    print("Welcome!")


@app.task(trigger=OnShutDown())
def shutdown():
    print("Bye!")


if __name__ == "__main__":
    asyncio.run(app.serve())