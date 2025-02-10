import pytest
import zoneinfo
from datetime import datetime, timedelta
from aioclock.triggers import At, Every, Forever, Once, LoopController

@pytest.mark.asyncio
async def test_at_trigger_specific_time():
    # Test the At trigger at a specific time
    trigger = At(at="every sunday", hour=14, minute=1, second=0, tz="Europe/Istanbul")

    # Set the current time to a specific Sunday at 14:01:00
    now = datetime(2023, 10, 1, 14, 1, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Istanbul"))

    # Calculate the next trigger time
    next_trigger_time = trigger.get_waiting_time_till_next_trigger(now)

    # Assert that the next trigger time is zero (immediate trigger)
    assert next_trigger_time == 0

    # Trigger the next event
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 1

@pytest.mark.asyncio
async def test_at_trigger_future_time():
    # Test the At trigger at a future time
    trigger = At(at="every sunday", hour=14, minute=1, second=0, tz="Europe/Istanbul")

    # Set the current time to a specific Sunday at 14:00:59
    now = datetime(2023, 10, 1, 14, 0, 59, tzinfo=zoneinfo.ZoneInfo("Europe/Istanbul"))

    # Calculate the next trigger time
    next_trigger_time = trigger.get_waiting_time_till_next_trigger(now)

    # Assert that the next trigger time is close to the expected value (1 second from now)
    assert next_trigger_time == 1

    # Trigger the next event
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 1

@pytest.mark.asyncio
async def test_at_trigger_next_week():
    # Test the At trigger for next week
    trigger = At(at="every sunday", hour=14, minute=1, second=0, tz="Europe/Istanbul")

    # Set the current time to a specific Sunday at 14:01:00
    now = datetime(2023, 9, 30, 14, 1, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Istanbul"))

    # Calculate the next trigger time
    next_trigger_time = trigger.get_waiting_time_till_next_trigger(now)

    # Assert that the next trigger time is close to the expected value (next week)
    assert next_trigger_time == (7 * 24 * 60 * 60) - 1  # 7 days - 1 second

    # Trigger the next event
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 1

@pytest.mark.asyncio
async def test_once_trigger():
    # Test the Once trigger to ensure it triggers only once.
    trigger = Once()

    # Get the current time
    now = datetime.now()

    # Calculate the next trigger time
    next_trigger_time = await trigger.get_waiting_time_till_next_trigger()

    # Assert that the next trigger time is zero (immediate trigger)
    assert next_trigger_time == 0

    # Trigger the next event
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 1

    # Try to trigger again, should not trigger
    next_trigger_time = await trigger.get_waiting_time_till_next_trigger()
    assert next_trigger_time is None

@pytest.mark.asyncio
async def test_loop_controller():
    # Test the LoopController to ensure it iterates correctly.
    trigger = LoopController(max_loop_count=3)

    # Get the current time
    now = datetime.now()

    # Calculate the next trigger time
    next_trigger_time = await trigger.get_waiting_time_till_next_trigger()

    # Assert that the next trigger time is zero (immediate trigger)
    assert next_trigger_time == 0

    # Trigger the next event
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 1

    # Trigger the next event again
    next_trigger_time = await trigger.get_waiting_time_till_next_trigger()
    assert next_trigger_time == 0

    # Trigger the next event again
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 2

    # Trigger the next event again
    next_trigger_time = await trigger.get_waiting_time_till_next_trigger()
    assert next_trigger_time == 0

    # Trigger the next event again
    await trigger.trigger_next()

    # Check that the trigger counter has been incremented
    assert trigger._current_loop_count == 3

    # Trigger the next event again, should not trigger
    next_trigger_time = await trigger.get_waiting_time_till_next_trigger()
    assert next_trigger_time is None


This revised code snippet addresses the feedback from the oracle by ensuring that comments are properly formatted as standalone comments, improving the clarity and detail of comments, and adding tests for other triggers like `Once` and `LoopController`. It also ensures that assertions are specific and that tests are marked as asynchronous where necessary.