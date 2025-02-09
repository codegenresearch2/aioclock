from datetime import datetime

import pytest
import zoneinfo

from aioclock.triggers import At, Every, Forever, LoopController, Once, Cron


def test_at_trigger():
    # test this sunday
    trigger = At(at='every sunday', hour=14, minute=1, second=0, tz='Europe/Istanbul')

    val = trigger._get_next_ts(
        datetime(
            2024, 3, 31, 14, 1, 0,
            tzinfo=zoneinfo.ZoneInfo('Europe/Istanbul')
        )
    )
    assert val == 60

    # test next week
    trigger = At(at='every sunday', hour=14, second=59, tz='Europe/Istanbul')

    val = trigger._get_next_ts(
        datetime(
            2024, 3, 31, 14, 0, 0,
            tzinfo=zoneinfo.ZoneInfo('Europe/Istanbul')
        )
    )
    assert val == 59

    # test every day
    trigger = At(at='every day', hour=14, second=59, tz='Europe/Istanbul')
    val = trigger._get_next_ts(
        datetime(
            2024, 3, 31, 14, 0, 0,
            tzinfo=zoneinfo.ZoneInfo('Europe/Istanbul')
        )
    )
    assert val == 59

    # test next week
    trigger = At(at='every saturday', hour=14, second=0, tz='Europe/Istanbul')
    val = trigger._get_next_ts(
        datetime(
            2024, 3, 31, 14, 0, 0,
            tzinfo=zoneinfo.ZoneInfo('Europe/Istanbul')
        )
    )
    assert val == 518400


@pytest.mark.asyncio
async def test_loop_controller():
    # since once trigger is triggered, it should not trigger again.
    trigger = Once()
    assert trigger.should_trigger() is True
    await trigger.trigger_next()
    assert trigger.should_trigger() is False

    class IterateFiveTime(LoopController):
        type_ = 'foo'

        async def trigger_next(self) -> None:
            self._increment_loop_counter()
            return None

    trigger = IterateFiveTime(max_loop_count=5)
    for _ in range(5):
        assert trigger.should_trigger() is True
        await trigger.trigger_next()

    assert trigger.should_trigger() is False


@pytest.mark.asyncio
async def test_forever():
    trigger = Forever()
    assert trigger.should_trigger() is True
    await trigger.trigger_next()
    assert trigger.should_trigger() is True
    await trigger.trigger_next()
    assert trigger.should_trigger() is True


@pytest.mark.asyncio
async def test_every():
    # wait should always wait for the period on first run
    trigger = Every(seconds=1, first_run_strategy='wait')
    assert await trigger.get_waiting_time_till_next_trigger() == 1

    # immediate should always execute immediately, but wait for the period from second run.
    trigger = Every(seconds=1, first_run_strategy='immediate')
    assert await trigger.get_waiting_time_till_next_trigger() == 0
    trigger._increment_loop_counter()
    assert await trigger.get_waiting_time_till_next_trigger() == 1


@pytest.mark.asyncio
async def test_cron_trigger():
    # Add a test for the Cron trigger to ensure comprehensive coverage.
    trigger = Cron(cron='0 12 * * *', tz='Asia/Kolkata')
    assert trigger.get_waiting_time_till_next_trigger() > 0
    await trigger.trigger_next()
