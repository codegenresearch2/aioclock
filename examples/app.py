import asyncio
from concurrent.futures import ThreadPoolExecutor

from aioclock import AioClock, Depends, Every, Group, OnShutDown, OnStartUp

# service1.py
group = Group(capacity=10)  # Added capacity limiter parameter

def dependency():
    return "Hello, world!"

def sync_dependency():
    return dependency()

executor = ThreadPoolExecutor(max_workers=5)  # Create a thread pool

@group.task(trigger=Every(seconds=1), metadata={'mutable': False})  # Clarified mutability warning for task metadata
async def my_task(val: str = Depends(sync_dependency)):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, val)  # Use thread pool to handle sync function
    print(result)

# app.py
app = AioClock()
app.include_group(group)

@app.task(trigger=OnStartUp(), metadata={'mutable': False})  # Clarified mutability warning for task metadata
async def startup(val: str = Depends(sync_dependency)):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, val)  # Use thread pool to handle sync function
    print("Welcome!", result)

@app.task(trigger=OnShutDown(), metadata={'mutable': False})  # Clarified mutability warning for task metadata
async def shutdown(val: str = Depends(sync_dependency)):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, val)  # Use thread pool to handle sync function
    print("Bye!", result)

if __name__ == "__main__":
    asyncio.run(app.serve())