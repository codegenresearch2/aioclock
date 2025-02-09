import asyncio
import threading
from aioclock import AioClock, Depends, Every, Group

# service1.py
group = Group()


def dependency():
    return "Hello, world!"


@group.task(trigger=Every(seconds=2))
def my_task(val: str = Depends(dependency)):
    print(f"Task is running on thread {threading.current_thread().ident}. {val}")


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