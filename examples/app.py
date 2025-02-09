import asyncio
import threading
from typing import Annotated

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency() -> str:
    return f"Hello, world! (Thread ID: {threading.get_ident()})"

@group.task(trigger=Every(seconds=2))
async def my_task(val: Annotated[str, Depends(dependency)]) -> None:
    print(f"Task value: {val} (Thread ID: {threading.get_ident()})")

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
sync_startup = group.sync_task(trigger=OnStartUp())
def startup(val: Annotated[str, Depends(dependency)]) -> str:
    print(f"Welcome! (Thread ID: {threading.get_ident()})")
    return val

@app.task(trigger=OnShutDown())
sync_shutdown = group.sync_task(trigger=OnShutDown())
def shutdown(val: Annotated[str, Depends(dependency)]) -> str:
    print(f"Bye! (Thread ID: {threading.get_ident()})")
    return val

if __name__ == "__main__":
    asyncio.run(app.serve())
