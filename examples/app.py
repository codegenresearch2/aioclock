import asyncio
from aioclock import AioClock, Depends, Every, Group

# service1.py
group = Group()


def dependency():
    return "Hello, world!"


@group.task(trigger=Every(seconds=5))
async def my_task(val: str = Depends(dependency)):
    print(f"Task running: {val} on thread {threading.get_ident()}")


@group.task(trigger=Every(seconds=5))
def sync_task(val: str = Depends(dependency)):
    print(f"Synchronous task running: {val} on thread {threading.get_ident()}")
    time.sleep(2)  # Simulating a blocking operation


# app.py
app = AioClock()
app.include_group(group)


@app.task(trigger=Every(seconds=5))
async def startup(val: str = Depends(dependency)):
    print(f"Welcome! {val} on thread {threading.get_ident()}")


@app.task(trigger=Every(seconds=5))
def shutdown(val: str = Depends(dependency)):
    print(f"Bye! {val} on thread {threading.get_ident()}")


if __name__ == "__main__":
    asyncio.run(app.serve())