import asyncio
import threading

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency():
    return f"Hello, world! (Thread ID: {threading.current_thread().ident})"

@group.task(trigger=Every(seconds=2))
async def my_task(val: str = Depends(dependency)):
    print(f"Task executed with value: {val} from Thread ID: {threading.current_thread().ident}")

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp())
sync_startup = lambda val: print(f"Welcome! (Thread ID: {threading.current_thread().ident})")

@app.task(trigger=OnShutDown())
sync_shutdown = lambda val: print(f"Bye! (Thread ID: {threading.current_thread().ident})")

if __name__ == "__main__":
    asyncio.run(app.serve())