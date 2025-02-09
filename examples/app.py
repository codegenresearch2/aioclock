import asyncio
from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group()


def dependency() -> str:
    return "Dependency value"


@group.task(trigger=Every(seconds=2.01))
def sync_task_1(val: str = Depends(dependency)) -> None:
    print(f"Sync task 1 (Thread {threading.get_ident()}) is running. {val}")


@group.task(trigger=Every(seconds=2.01))
def sync_task_2(val: str = Depends(dependency)) -> str:
    print(f"Sync task 2 (Thread {threading.get_ident()}) is running. {val}")
    # Simulate a blocking operation
    import time
    time.sleep(1)
    return "Sync task 2 completed"


@group.task(trigger=Every(seconds=2.01))
async def async_task(val: str = Depends(dependency)) -> None:
    print(f"Async task (Thread {threading.get_ident()}) is running. {val}")


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=OnStartUp())
def startup(val: str = Depends(dependency)) -> None:
    print(f"Startup task (Thread {threading.get_ident()}) is running. {val}")


@app.task(trigger=OnShutDown())
def shutdown(val: str = Depends(dependency)) -> None:
    print(f"Shutdown task (Thread {threading.get_ident()}) is running. {val}")


if __name__ == "__main__":
    asyncio.run(app.serve())