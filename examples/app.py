import asyncio
import threading
import time

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency():
    return "Thread context: " + threading.current_thread().name


@group.task(trigger=Every(seconds=3))
def sync_task_1():
    print("Sync task 1 executed by thread {}".format(threading.current_thread().ident))
    return "Sync task 1 completed"


@group.task(trigger=Every(seconds=3))
def sync_task_2():
    print("Sync task 2 executed by thread {}".format(threading.current_thread().ident))
    return "Sync task 2 completed"


@group.task(trigger=Every(seconds=2.01))
async def async_task():
    print("Async task executed by thread {}".format(threading.current_thread().ident))


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup():
    print("Startup executed by thread {}".format(threading.current_thread().ident))
    return "Startup completed"


@app.task(trigger=OnShutDown())
def shutdown():
    print("Shutdown executed by thread {}".format(threading.current_thread().ident))
    return "Shutdown completed"


if __name__ == "__main__":
    asyncio.run(app.serve())