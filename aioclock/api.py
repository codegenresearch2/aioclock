from aioclock import AioClock, Once
from aioclock.api import run_specific_task

app = AioClock()

@app.task(trigger=Once())
async def main():
    """
    This function prints 'Hello World' and returns a value.
    """
    print('Hello World')

async def some_other_func():
    await run_specific_task(app._tasks[0].id, app)
