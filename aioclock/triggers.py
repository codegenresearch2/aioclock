"""
This module defines various trigger classes for scheduling tasks in an asynchronous application using the `aioclock` framework.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Annotated, Generic, Literal, TypeVar, Union

import zoneinfo
from annotated_types import Interval
from pydantic import BaseModel, Field, PositiveInt, model_validator

from aioclock.custom_types import EveryT, PositiveNumber, Triggers

TriggerTypeT = TypeVar("TriggerTypeT")

class BaseTrigger(BaseModel, ABC, Generic[TriggerTypeT]):
    """
    Base class for all triggers.
    A trigger is a way to determine when the event should be triggered. It can be based on time, or some other condition.

    Attributes:
        type_: Type of the trigger. It is a string, which is used to identify the trigger's name.
        expected_trigger_time: The time at which the trigger is expected to trigger the event.
    """
    type_: TriggerTypeT
    expected_trigger_time: Union[datetime, None] = None

    @abstractmethod
    async def trigger_next(self) -> None:
        """
        `trigger_next` keeps track of the event, and triggers the event.
        The function shall return when the event is triggered and should be executed.
        """
        pass

    def should_trigger(self) -> bool:
        """
        `should_trigger` checks if the event should be triggered or not.
        If not, then the event will not be triggered anymore.
        You can save the state of the trigger and task inside the instance, and then check if the event should be triggered or not.
        """
        return True

    @abstractmethod
    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:
        """
        Returns the time in seconds, after which the event should be triggered.
        Returns None, if the event should not trigger anymore.
        """
        ...

class Forever(BaseTrigger[Literal[Triggers.FOREVER]]):
    """A trigger that is always triggered immediately.

    Attributes:
        type_: Type of the trigger. It is a string, which is used to identify the trigger's name.
    """
    type_: Literal[Triggers.FOREVER] = Triggers.FOREVER

    def should_trigger(self) -> bool:
        return True

    async def trigger_next(self) -> None:
        return None

    async def get_waiting_time_till_next_trigger(self):
        return 0

class LoopController(BaseTrigger, ABC, Generic[TriggerTypeT]):
    """
    Base class for all triggers that have loop control.

    Attributes:
        type_: Type of the trigger. It is a string, which is used to identify the trigger's name.
        max_loop_count: The maximum number of times the event should be triggered.
            If set to 3, then 4th time the event will not be triggered.
            If set to None, it will keep running forever.
        _current_loop_count: Current loop count, which is used to keep track of the number of times the event has been triggered.
    """
    type_: TriggerTypeT
    _current_loop_count: int = 0
    max_loop_count: Union[PositiveInt, None] = None

    @model_validator(mode="after")
    def validate_loop_controll(self):
        if "_current_loop_count" in self.model_fields_set:
            raise ValueError("