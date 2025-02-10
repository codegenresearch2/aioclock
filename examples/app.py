import asyncio
import threading

from aioclock import AioClock, Depends, Every, Group

# service1.py
group = Group()


def dependency():
    return "Hello, world!"


@group.task(trigger=Every(seconds=1))
async def my_task(val: str = Depends(dependency)):
    print(f"Task executed by thread {threading.current_thread().name}: {val}")


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=Every(seconds=1))
def startup(val: str = Depends(dependency)):
    print(f"Startup executed by thread {threading.current_thread().name}: {val}")


@app.task(trigger=Every(seconds=1))
def shutdown(val: str = Depends(dependency)):
    print(f"Shutdown executed by thread {threading.current_thread().name}: {val}")


if __name__ == "__main__":
    asyncio.run(app.serve())