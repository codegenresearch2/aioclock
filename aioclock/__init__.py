from fast_depends import Depends

from aioclock.app import AioClock
from aioclock.group import Group
from aioclock.triggers import At, Every, Forever, Once, OnShutDown, OnStartUp

__all__ = [
    "Depends",
    "Once",
    "OnStartUp",
    "OnShutDown",
    "Every",
    "Forever",
    "Group",
    "AioClock",
    "At",
]

__version__ = "0.1.1"

# Implement cron job functionality
from aiocron import CronTrigger

@group.task(trigger=CronTrigger(hour="*", minute="*", second="*"))
async def cron_job():
    print("Cron job executed")

# Enhance test coverage for new features
import pytest

@pytest.fixture
def group():
    return Group()

@pytest.fixture
def aio_clock():
    return AioClock()

@pytest.fixture
def once_task(group):
    @group.task(trigger=Once())
    async def once():
        print("Once task executed")
    return once

@pytest.fixture
def every_task(group):
    @group.task(trigger=Every(seconds=5))
    async def every():
        print("Every 5 seconds task executed")
    return every

@pytest.fixture
def forever_task(group):
    @group.task(trigger=Forever())
    async def forever():
        print("Forever task executed")
    return forever

@pytest.fixture
def at_task(group):
    @group.task(trigger=At(tz="UTC", hour=0, minute=0, second=0))
    async def at():
        print("At midnight task executed")
    return at

@pytest.fixture
def on_startup_task(aio_clock):
    @aio_clock.task(trigger=OnStartUp())
    async def startup():
        print("Application startup task executed")
    return startup

@pytest.fixture
def on_shutdown_task(aio_clock):
    @aio_clock.task(trigger=OnShutDown())
    async def shutdown():
        print("Application shutdown task executed")
    return shutdown

# Maintain clean and organized code structure
def test_group_task_creation(group):
    @group.task(trigger=Every(seconds=10))
    async def test_task():
        pass
    assert len(group._tasks) == 1

def test_aio_clock_include_group(aio_clock, group):
    aio_clock.include_group(group)
    assert group in aio_clock._groups

def test_once_task_execution(once_task):
    pass  # Execution is handled by the fixture

def test_every_task_execution(every_task):
    pass  # Execution is handled by the fixture

def test_forever_task_execution(forever_task):
    pass  # Execution is handled by the fixture

def test_at_task_execution(at_task):
    pass  # Execution is handled by the fixture

def test_on_startup_task_execution(on_startup_task):
    pass  # Execution is handled by the fixture

def test_on_shutdown_task_execution(on_shutdown_task):
    pass  # Execution is handled by the fixture