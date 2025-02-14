"""\nTriggers are used to determine when the event should be triggered. It can be based on time, or some other condition.\nYou can create custom triggers by inheriting from `BaseTrigger` class.\n\n!!! info "Don't run CPU intensive or thread-block IO tasks"\n    AioClock's triggers are all running in async, only on one CPU.
    So, if you run a CPU intensive task, or a task that blocks the thread, then it will block the entire event loop.
    If you have a sync IO task, then it's recommended to use `run_in_executor` to run the task in a separate thread.\n    Or use similar libraries like `asyncer` or `trio` to run the task in a separate thread.\n"""\n\nimport asyncio\nfrom abc import ABC, abstractmethod\nfrom copy import deepcopy\nfrom datetime import datetime, timedelta\nfrom typing import Annotated, Generic, Literal, TypeVar, Union\n\nimport zoneinfo\nfrom annotated_types import Interval\nfrom pydantic import BaseModel, Field, PositiveInt, model_validator\n\nfrom aioclock.custom_types import EveryT, PositiveNumber, Triggers\n\nTriggerTypeT = TypeVar("TriggerTypeT")\n\n\nclass BaseTrigger(BaseModel, ABC, Generic[TriggerTypeT]):\n    """\n    Base class for all triggers.\n    A trigger is a way to determine when the event should be triggered. It can be based on time, or some other condition.\n\n    The way triggers are used is as follows:\n        1. An async function which is a task, is decorated with framework, and trigger is the argument for the decorator\n        2. `get_waiting_time_till_next_trigger` is called to get the time in seconds, after which the event should be triggered.\n        3. If the time is not None, then it logs the time that is predicted for the event to be triggered.\n        4. `trigger_next` is called immediately after that, which triggers the event.\n\n    You can create triggers by yourself, by inheriting from `BaseTrigger` class.\n\n    Example:\n        \n        from aioclock.triggers import BaseTrigger\n        from typing import Literal\n\n        class Forever(BaseTrigger[Literal["Forever"]]):\n            type_: Literal["Forever"] = "Forever"\n\n            def should_trigger(self) -> bool:\n                return True\n\n            async def trigger_next(self) -> None:\n                return None\n\n            async def get_waiting_time_till_next_trigger(self):\n                if self.should_trigger():\n                    return 0\n                return None\n        \n\n    Attributes:\n        type_: Type of the trigger. It is a string, which is used to identify the trigger's name.
            You can change the type by using `Generic` type when inheriting from `BaseTrigger`.
    """\n\n    type_: TriggerTypeT\n    expected_trigger_time: Union[datetime, None] = None\n\n    @abstractmethod\n    async def trigger_next(self) -> None:\n        """
        `trigger_next` keeps track of the event, and triggers the event.
        The function shall return when the event is triggered and should be executed.
        """\n\n    def should_trigger(self) -> bool:\n        """
        `should_trigger` checks if the event should be triggered or not.
        If not, then the event will not be triggered anymore.
        You can save the state of the trigger and task inside the instance, and then check if the event should be triggered or not.
        For instance, in `LoopController` trigger, it keeps track of the number of times the event has been triggered,
        and then checks if the event should be triggered or not.
        """\n        return True\n\n    @abstractmethod\n    async def get_waiting_time_till_next_trigger(self) -> Union[float, None]:\n        """
        Returns the time in seconds, after which the event should be triggered.
        Returns None, if the event should not trigger anymore.
        """\n        ...\n\n\nclass Forever(BaseTrigger[Literal[Triggers.FOREVER]]):\n    """A trigger that is always triggered immediately.

    Example:
        
            from aioclock import AioClock, Forever

            app = AioClock()

            # instead of this:
            async def my_task():
                while True:
                    try:
                        await asyncio.sleep(3)
                        1/0
                    except DivisionByZero:
                        pass

            # use this:
            @app.task(trigger=Forever())
            async def my_task():
                await asyncio.sleep(3)
                1/0
        

    Attributes:
        type_: Type of the trigger. It is a string, which is used to identify the trigger's name.\n            You can change the type by using `Generic` type when inheriting from `BaseTrigger`.\n    """\n\n    type_: Literal[Triggers.FOREVER] = Triggers.FOREVER\n\n    def should_trigger(self) -> bool:\n        return True\n\n    async def trigger_next(self) -> None:\n        return None\n\n    async def get_waiting_time_till_next_trigger(self):\n        return 0\n\n\nclass LoopController(BaseTrigger, ABC, Generic[TriggerTypeT]):\n    """\n    Base class for all triggers that have loop control.\n\n    Attributes:\n        type_: Type of the trigger. It is a string, which is used to identify the trigger's name.
            You can change the type by using `Generic` type when inheriting from `LoopController`.

        max_loop_count: The maximum number of times the event should be triggered.
            If set to 3, then the 4th time the event will not be triggered.
            If set to None, it will keep running forever.
            This is available for all triggers that inherit from `LoopController`.

        _current_loop_count: Current loop count, which is used to keep track of the number of times the event has been triggered.
            Private attribute, should not be accessed directly.
            This is available for all triggers that inherit from `LoopController`.
    """\n\n    type_: TriggerTypeT\n    _current_loop_count: int = 0\n    max_loop_count: Union[PositiveInt, None] = None\n\n    @model_validator(mode="after")\n    def validate_loop_controll(self):\n        if "_current_loop_count" in self.model_fields_set:\n            raise ValueError("_current_loop_count is a private attribute, should not be provided.")\n        return self\n\n    def _increment_loop_counter(self) -> None:\n        self._current_loop_count += 1\n\n    def should_trigger(self) -> bool:\n        if self.max_loop_count is None:\n            return True\n        if self._current_loop_count < self.max_loop_count:\n            return True\n        return False\n\n    async def get_waiting_time_till_next_trigger(self):\n        return 0\n\n\nclass Once(LoopController[Literal[Triggers.ONCE]]):\n    """A trigger that is triggered only once. It is used to trigger the event only once, and then stop.

    Example:
        
        from aioclock import AioClock, Once
        app = AioClock()

        @app.task(trigger=Once())
        async def task():
            print("Hello World!")
        
    """\n\n    type_: Literal[Triggers.ONCE] = Triggers.ONCE\n    max_loop_count: Literal[1] = 1\n\n    async def trigger_next(self) -> None:\n        self._increment_loop_counter()\n        return None\n\n    async def get_waiting_time_till_next_trigger(self):\n        if self._current_loop_count == 0:\n            return 0\n        return None\n\n\nclass OnStartUp(LoopController[Literal[Triggers.ON_START_UP]]):\n    """Just like Once, but it triggers the event only once, when the application starts up.

    Example:
        
        from aioclock import AioClock, OnStartUp
        app = AioClock()

        @app.task(trigger=OnStartUp())
        async def task():
            print("Hello World!")
        
    """\n\n    type_: Literal[Triggers.ON_START_UP] = Triggers.ON_START_UP\n    max_loop_count: Literal[1] = 1\n\n    async def trigger_next(self) -> None:\n        self._increment_loop_counter()\n        return None\n\n    async def get_waiting_time_till_next_trigger(self):\n        if self._current_loop_count == 0:\n            return 0\n        return None\n\n\nclass OnShutDown(LoopController[Literal[Triggers.ON_SHUT_DOWN]]):\n    """Just like Once, but it triggers the event only once, when the application shuts down.

    Example:
        
        from aioclock import AioClock, OnShutDown
        app = AioClock()

        @app.task(trigger=OnShutDown())
        async def task():
            print("Hello World!")
        
    """\n\n    type_: Literal[Triggers.ON_SHUT_DOWN] = Triggers.ON_SHUT_DOWN\n    max_loop_count: Literal[1] = 1\n\n    async def trigger_next(self) -> None:\n        self._increment_loop_counter()\n        return None\n\n    async def get_waiting_time_till_next_trigger(self):\n        if self._current_loop_count == 0:\n            return 0\n        return None\n\n\nclass Every(LoopController[Literal[Triggers.EVERY]]):\n    """A trigger that is triggered every x time units.

    Example:
        
        from aioclock import AioClock, Every
        app = AioClock()

        @app.task(trigger=Every(seconds=3))
        async def task():
            print("Hello World!")
        

    Attributes:
        first_run_strategy: Strategy to use for the first run.
            If `immediate`, then the event will be triggered immediately,
                and then wait for the time to trigger the event again.
            If `wait`, then the event will wait for the time to trigger the event for the first time.

        seconds: Seconds to wait before triggering the event.
        minutes: Minutes to wait before triggering the event.
        hours: Hours to wait before triggering the event.
        days: Days to wait before triggering the event.
        weeks: Weeks to wait before triggering the event.
        max_loop_count: The maximum number of times the event should be triggered.
    """\n\n    type_: Literal[Triggers.EVERY] = Triggers.EVERY\n    first_run_strategy: Literal["immediate", "wait"] = "wait"\n    seconds: Union[PositiveNumber, None] = None\n    minutes: Union[PositiveNumber, None] = None\n    hours: Union[PositiveNumber, None] = None\n    days: Union[PositiveNumber, None] = None\n    weeks: Union[PositiveNumber, None] = None\n    max_loop_count: Union[PositiveInt, None] = None\n\n    @model_validator(mode="after")\n    def validate_time_units(self):\n        if (\n            self.seconds is None\n            and self.minutes is None\n            and self.hours is None\n            and self.days is None\n            and self.weeks is None\n        ):\n            raise ValueError("At least one time unit must be provided.")\n\n        return self\n\n    @property\n    def to_seconds(self) -> float:\n        result = self.seconds or 0\n        if self.weeks is not None:\n            result += self.weeks * 604800\n        if self.days is not None:\n            result += self.days * 86400\n        if self.hours is not None:\n            result += self.hours * 3600\n        if self.minutes is not None:\n            result += self.minutes * 60\n\n        return result\n\n    async def trigger_next(self) -> None:\n        self._increment_loop_counter()\n        if self._current_loop_count == 1 and self.first_run_strategy == "immediate":\n            return None\n        await asyncio.sleep(self.to_seconds)\n        return None\n\n    async def get_waiting_time_till_next_trigger(self):\n        # not incremented yet, so the counter is 0\n        if self._current_loop_count == 0 and self.first_run_strategy == "immediate":\n            return 0\n\n        if self.should_trigger():\n            return self.to_seconds\n        return None\n\n\nWEEK_TO_SECOND = 604800\n\n\nclass At(LoopController[Literal[Triggers.AT]]):\n    """A trigger that is triggered at a specific time.

    Example:
        
        from aioclock import AioClock, At

        app = AioClock()

        @app.task(trigger=At(hour=12, minute=30, tz="Asia/Kolkata"))
        async def task():
            print("Hello World!")
        

    Attributes:
        second: Second to trigger the event.
        minute: Minute to trigger the event.
        hour: Hour to trigger the event.
        at: Day of week to trigger the event. You would get inline typing support when using the trigger.
        tz: Timezone to use for the event.
        max_loop_count: The maximum number of times the event should be triggered.
    """\n\n    type_: Literal[Triggers.AT] = Triggers.AT\n    max_loop_count: Union[PositiveInt, None] = None\n    second: Annotated[int, Interval(ge=0, le=59)] = 0\n    minute: Annotated[int, Interval(ge=0, le=59)] = 0\n    hour: Annotated[int, Interval(ge=0, le=24)] = 0\n    at: Literal[\n        "every monday",\n        "every tuesday",\n        "every wednesday",\n        "every thursday",\n        "every friday",\n        "every saturday",\n        "every sunday",\n        "every day",\n    ] = "every day"\n    tz: str\n\n    @model_validator(mode="after")\n    def validate_time_units(self):\n        if self.second is None and self.minute is None and self.hour is None:\n            raise ValueError("At least one time unit must be provided.")\n\n        if self.tz is not None:\n            try:\n                zoneinfo.ZoneInfo(self.tz)\n            except Exception as error:\n                raise ValueError(f"Invalid timezone provided: {error}")\n\n        return self\n\n    def _shift_to_week(self, target_time: datetime, tz_aware_now: datetime):\n        target_weekday: dict[EveryT, Union[int, None]] = {\n            "every monday": 0,\n            "every tuesday": 1,\n            "every wednesday": 2,\n            "every thursday": 3,\n            "every friday": 4,\n            "every saturday": 5,\n            "every sunday": 6,\n            "every day": None,\n        }[self.at]\n\n        if target_weekday is None:\n            if target_time < tz_aware_now:\n                target_time += timedelta(days=1)\n            return target_time\n\n        days_ahead = target_weekday - tz_aware_now.weekday()  # type: ignore\n        if days_ahead <= 0:\n            days_ahead += 7\n\n        if self.at == "every day":\n            target_time += timedelta(days=(1 if target_time < tz_aware_now else 0))\n            return target_time\n\n        # 1 second error\n        error_margin = WEEK_TO_SECOND - 1\n        if days_ahead == 7 and target_time.timestamp() - tz_aware_now.timestamp() < error_margin:\n            # date is today, and event is about to be triggered today. so no need to shift to 7 days.\n            return target_time\n\n        return target_time + timedelta(days_ahead)\n\n    def _get_next_ts(self, now: datetime) -> float:\n        target_time = deepcopy(now).replace(\n            hour=self.hour, minute=self.minute, second=self.second, microsecond=0\n        )\n        target_time = self._shift_to_week(target_time, now)\n        return (target_time - now).total_seconds()\n\n    def get_sleep_time(self):\n        now = datetime.now(tz=zoneinfo.ZoneInfo(self.tz))\n        sleep_for = self._get_next_ts(now)\n        return sleep_for\n\n    async def get_waiting_time_till_next_trigger(self):\n        return self.get_sleep_time()\n\n    async def trigger_next(self) -> None:\n        self._increment_loop_counter()\n        await asyncio.sleep(self.get_sleep_time())\n\n\nTriggerT = Annotated[\n    Union[Forever, Once, Every, At, OnStartUp, OnShutDown], Field(discriminator="type_")\n]