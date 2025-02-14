from fast_depends import Depends
from croniter import croniter
from datetime import datetime

from aioclock.app import AioClock
from aioclock.group import Group
from aioclock.triggers import At, Every, Forever, Once, OnShutDown, OnStartUp
from aioclock.custom_types import Triggers

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

class EventState:
    def __init__(self):
        self.state = {}

    def set_state(self, trigger, state):
        self.state[trigger] = state

    def get_state(self, trigger):
        return self.state.get(trigger, False)

event_state = EventState()

class CronTrigger:
    def __init__(self, cron_format):
        self.cron_format = cron_format

    def should_trigger(self, now):
        return croniter.match(self.cron_format, now)

class TimeTrigger:
    def __init__(self, tz, hour, minute, second):
        self.tz = tz
        self.hour = hour
        self.minute = minute
        self.second = second

    def should_trigger(self, now):
        return (
            now.hour == self.hour
            and now.minute == self.minute
            and now.second == self.second
        )

class EveryTrigger:
    def __init__(self, seconds):
        self.seconds = seconds
        self.last_trigger = datetime.now()

    def should_trigger(self, now):
        if (now - self.last_trigger).total_seconds() >= self.seconds:
            self.last_trigger = now
            return True
        return False

class TriggerManager:
    def __init__(self):
        self.triggers = {}

    def add_trigger(self, trigger_type, trigger):
        self.triggers[trigger_type] = trigger

    def should_trigger(self, trigger_type, now):
        trigger = self.triggers.get(trigger_type)
        if trigger:
            return trigger.should_trigger(now)
        return False

trigger_manager = TriggerManager()


This code introduces a `TriggerManager` class that manages different types of triggers. It also introduces `CronTrigger`, `TimeTrigger`, and `EveryTrigger` classes to handle cron, time, and every triggers respectively. The `EventState` class is used to manage the state of events. The `should_trigger` method in each trigger class checks if the event should be triggered based on the current time.