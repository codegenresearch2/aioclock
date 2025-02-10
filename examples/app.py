import asyncio
import threading
from time import sleep
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency():
    return "Hello, world!"


@group.task(trigger=Every(seconds=2))
async def task_with_dependency(val: str = Depends(dependency)):
    print(f"Task is running with value: {val} on thread: {threading.get_ident()}")
    sleep(1)  # Simulating a blocking operation


@group.task(trigger=Every(seconds=2.01))
def another_task(val: str = Depends(dependency)):
    print(f"Another task is running with value: {val} on thread: {threading.get_ident()}")
    sleep(1)  # Simulating a blocking operation


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup(val: str = Depends(dependency)):
    print(f"Welcome! {val} on thread: {threading.get_ident()}")


@app.task(trigger=OnShutDown())
def shutdown(val: str = Depends(dependency)):
    print(f"Bye! {val} on thread: {threading.get_ident()}")


if __name__ == "__main__":
    asyncio.run(app.serve())