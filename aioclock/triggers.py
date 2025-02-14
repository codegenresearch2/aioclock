import asyncio
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Annotated, Generic, Literal, TypeVar, Union

import zoneinfo
from annotated_types import Interval
from croniter import croniter
from pydantic import BaseModel, Field, PositiveInt, model_validator

from aioclock.custom_types import EveryT, PositiveNumber, Triggers

TriggerTypeT = TypeVar("TriggerTypeT")

class BaseTrigger(BaseModel, ABC, Generic[TriggerTypeT]):
    type_: TriggerTypeT
    expected_trigger_time: Union[datetime, None] = None

    @abstractmethod
    async def trigger_next(self) -> None:
        ...

    def should_trigger(self) -> bool:
        return True

    @abstractmethod
    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        ...

class CronTrigger(BaseTrigger[Literal[Triggers.CRON]]):
    type_: Literal[Triggers.CRON] = Triggers.CRON
    cron: str
    tz: str

    def get_waiting_time_till_next_trigger(self, now: datetime = None) -> float:
        if now is None:
            now = datetime.now(tz=zoneinfo.ZoneInfo(self.tz))
        cron_iter = croniter(self.cron, now, ret_type=datetime, timezone=self.tz)
        return (cron_iter.get_next(datetime) - now).total_seconds()

    async def trigger_next(self) -> None:
        await asyncio.sleep(self.get_waiting_time_till_next_trigger())

class ForeverTrigger(BaseTrigger[Literal[Triggers.FOREVER]]):
    type_: Literal[Triggers.FOREVER] = Triggers.FOREVER

    def should_trigger(self) -> bool:
        return True

    async def trigger_next(self) -> None:
        return None

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        return 0

class LoopControllerTrigger(BaseTrigger, ABC, Generic[TriggerTypeT]):
    type_: TriggerTypeT
    _current_loop_count: int = 0
    max_loop_count: Union[PositiveInt, None] = None

    @model_validator(mode="after")
    def validate_loop_control(self):
        if "_current_loop_count" in self.model_fields_set:
            raise ValueError("_current_loop_count is a private attribute, should not be provided.")
        return self

    def _increment_loop_counter(self) -> None:
        self._current_loop_count += 1

    def should_trigger(self) -> bool:
        if self.max_loop_count is None:
            return True
        if self._current_loop_count < self.max_loop_count:
            return True
        return False

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        return 0

class OnceTrigger(LoopControllerTrigger[Literal[Triggers.ONCE]]):
    type_: Literal[Triggers.ONCE] = Triggers.ONCE
    max_loop_count: Literal[1] = 1

    async def trigger_next(self) -> None:
        self._increment_loop_counter()
        return None

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        if self._current_loop_count == 0:
            return 0
        return None

class OnStartUpTrigger(LoopControllerTrigger[Literal[Triggers.ON_START_UP]]):
    type_: Literal[Triggers.ON_START_UP] = Triggers.ON_START_UP
    max_loop_count: Literal[1] = 1

    async def trigger_next(self) -> None:
        self._increment_loop_counter()
        return None

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        if self._current_loop_count == 0:
            return 0
        return None

class OnShutDownTrigger(LoopControllerTrigger[Literal[Triggers.ON_SHUT_DOWN]]):
    type_: Literal[Triggers.ON_SHUT_DOWN] = Triggers.ON_SHUT_DOWN
    max_loop_count: Literal[1] = 1

    async def trigger_next(self) -> None:
        self._increment_loop_counter()
        return None

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        if self._current_loop_count == 0:
            return 0
        return None

class EveryTrigger(LoopControllerTrigger[Literal[Triggers.EVERY]]):
    type_: Literal[Triggers.EVERY] = Triggers.EVERY
    first_run_strategy: Literal["immediate", "wait"] = "wait"
    seconds: Union[PositiveNumber, None] = None
    minutes: Union[PositiveNumber, None] = None
    hours: Union[PositiveNumber, None] = None
    days: Union[PositiveNumber, None] = None
    weeks: Union[PositiveNumber, None] = None
    max_loop_count: Union[PositiveInt, None] = None

    @model_validator(mode="after")
    def validate_time_units(self):
        if (
            self.seconds is None
            and self.minutes is None
            and self.hours is None
            and self.days is None
            and self.weeks is None
        ):
            raise ValueError("At least one time unit must be provided.")
        return self

    @property
    def to_seconds(self) -> float:
        result = self.seconds or 0
        if self.weeks is not None:
            result += self.weeks * 604800
        if self.days is not None:
            result += self.days * 86400
        if self.hours is not None:
            result += self.hours * 3600
        if self.minutes is not None:
            result += self.minutes * 60
        return result

    async def trigger_next(self) -> None:
        self._increment_loop_counter()
        if self._current_loop_count == 1 and self.first_run_strategy == "immediate":
            return None
        await asyncio.sleep(self.to_seconds)
        return None

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        if self._current_loop_count == 0 and self.first_run_strategy == "immediate":
            return 0
        if self.should_trigger():
            return self.to_seconds
        return None

WEEK_TO_SECOND = 604800

class AtTrigger(LoopControllerTrigger[Literal[Triggers.AT]]):
    type_: Literal[Triggers.AT] = Triggers.AT
    max_loop_count: Union[PositiveInt, None] = None
    second: Annotated[int, Interval(ge=0, le=59)] = 0
    minute: Annotated[int, Interval(ge=0, le=59)] = 0
    hour: Annotated[int, Interval(ge=0, le=24)] = 0
    at: Literal[
        "every monday",
        "every tuesday",
        "every wednesday",
        "every thursday",
        "every friday",
        "every saturday",
        "every sunday",
        "every day",
    ] = "every day"
    tz: str

    @model_validator(mode="after")
    def validate_time_units(self):
        if self.second is None and self.minute is None and self.hour is None:
            raise ValueError("At least one time unit must be provided.")
        if self.tz is not None:
            try:
                zoneinfo.ZoneInfo(self.tz)
            except Exception as error:
                raise ValueError(f"Invalid timezone provided: {error}")
        return self

    def _shift_to_week(self, target_time: datetime, tz_aware_now: datetime) -> datetime:
        target_weekday: dict[EveryT, Union[int, None]] = {
            "every monday": 0,
            "every tuesday": 1,
            "every wednesday": 2,
            "every thursday": 3,
            "every friday": 4,
            "every saturday": 5,
            "every sunday": 6,
            "every day": None,
        }

        if target_weekday[self.at] is None:
            if target_time < tz_aware_now:
                target_time += timedelta(days=1)
            return target_time

        days_ahead = target_weekday[self.at] - tz_aware_now.weekday()  # type: ignore
        if days_ahead <= 0:
            days_ahead += 7

        if self.at == "every day":
            target_time += timedelta(days=(1 if target_time < tz_aware_now else 0))
            return target_time

        error_margin = WEEK_TO_SECOND - 1
        if days_ahead == 7 and target_time.timestamp() - tz_aware_now.timestamp() < error_margin:
            return target_time

        return target_time + timedelta(days=days_ahead)

    def _get_next_ts(self, now: datetime) -> float:
        target_time = deepcopy(now).replace(
            hour=self.hour, minute=self.minute, second=self.second, microsecond=0
        )
        target_time = self._shift_to_week(target_time, now)
        return (target_time - now).total_seconds()

    def get_sleep_time(self) -> float:
        now = datetime.now(tz=zoneinfo.ZoneInfo(self.tz))
        sleep_for = self._get_next_ts(now)
        return sleep_for

    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        return self.get_sleep_time()

    async def trigger_next(self) -> None:
        self._increment_loop_counter()
        await asyncio.sleep(self.get_sleep_time())

TriggerT = Annotated[
    Union[CronTrigger, ForeverTrigger, OnceTrigger, EveryTrigger, AtTrigger, OnStartUpTrigger, OnShutDownTrigger],
    Field(discriminator="type_"),
]


This rewritten code implements cron job support by adding a new `CronTrigger` class that uses the `croniter` library to calculate the waiting time till the next trigger. The `BaseTrigger` and `LoopControllerTrigger` classes have been renamed to follow consistent trigger naming conventions. The test coverage for new features has been enhanced by adding a `test_cron` function to the `tests/test_triggers.py` file.