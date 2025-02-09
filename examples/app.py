import asyncio
import threading
import time

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency() -> str:
    return 'Hello, world!'  # Simplified dependency function

@group.task(trigger=Every(seconds=2))
async def my_async_task(val: str = Depends(dependency)):
    print(f'Async Task value: {val} (Thread ID: {threading.current_thread().ident})')

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
def sync_task_1():
    print(f'Startup Task (Thread ID: {threading.current_thread().ident})')
    time.sleep(1)  # Simulate blocking operation

@app.task(trigger=OnShutDown())
def sync_task_2():
    print(f'Shutdown Task (Thread ID: {threading.current_thread().ident})')
    time.sleep(1)  # Simulate blocking operation

if __name__ == '__main__':
    asyncio.run(app.serve())