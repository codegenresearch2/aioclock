from datetime import datetime

import pytest
import zoneinfo
from croniter import croniter

from aioclock.triggers import LoopController, Triggers

class Cron(LoopController[Triggers.CRON]):
    """A trigger that is triggered at a specific time, using cron job format.

    Example:
        
        from aioclock import AioClock, Cron

        app = AioClock()

        @app.task(trigger=Cron(cron="0 12 * * *", tz="Asia/Kolkata"))
        async def task():
            print("Hello World!")
        

    Attributes:
        cron: Cron job format to trigger the event.
        tz: Timezone to use for the event.
        max_loop_count: The maximum number of times the event should be triggered.
    """

    type_: Triggers.CRON = Triggers.CRON
    max_loop_count: Union[PositiveInt, None] = None
    cron: str
    tz: str

    @model_validator(mode="after")
    def validate_time_units(self):
        if self.tz is not None:
            try:
                zoneinfo.ZoneInfo(self.tz)
            except Exception as error:
                raise ValueError(f"Invalid timezone provided: {error}")

        if croniter.is_valid(self.cron) is False:
            raise ValueError("Invalid cron format provided.")
        return self

    def get_waiting_time_till_next_trigger(self, now: Union[datetime, None] = None):
        if now is None:
            now = datetime.now(tz=zoneinfo.ZoneInfo(self.tz))

        cron_iter = croniter(self.cron, now)
        next_dt: datetime = cron_iter.get_next(datetime)
        return (next_dt - now).total_seconds()

    async def trigger_next(self) -> None:
        self._increment_loop_counter()
        await asyncio.sleep(self.get_waiting_time_till_next_trigger())

@pytest.mark.asyncio
async def test_cron():
    trigger = Cron(cron="0 12 * * *", tz="Asia/Kolkata")
    assert trigger.get_waiting_time_till_next_trigger(datetime(2024, 3, 31, 11, 59, 59, tzinfo=zoneinfo.ZoneInfo("Asia/Kolkata"))) == 61

    trigger = Cron(cron="* * * * *", tz="Asia/Kolkata")
    assert trigger.get_waiting_time_till_next_trigger(datetime(2024, 3, 31, 11, 59, 59, tzinfo=zoneinfo.ZoneInfo("Asia/Kolkata"))) == 1

    with pytest.raises(ValueError):
        Cron(cron="invalid", tz="Asia/Kolkata")

    with pytest.raises(ValueError):
        Cron(cron="0 12 * * *", tz="invalid")


In the provided code, I have rewritten the `test_at_trigger` function to use the `Cron` trigger instead. This is because the user prefers to implement cron job functionality. I have also added a new `test_cron` function to test the `Cron` trigger. The `Cron` trigger uses the `croniter` library to validate the cron format and calculate the waiting time till the next trigger. I have also added input validation for the timezone. The code is now more readable and organized, and it follows the user's preferences.