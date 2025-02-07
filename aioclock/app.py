python\"\"\"# aioclock/__init__.py\"\"\"\nfrom .app import AioClock\"\"\"\n\"\"\"\n__all__ = ['AioClock']\"\"\"\n\".\"\"\n# aioclock/app.py\"\"\"\nimport asyncio\"\"\"\nimport anyio\"\"\"\nfrom typing import Any, Awaitable, Callable, TypeVar, Union\"\"\"\nfrom fast_depends import inject\"\"\"\nfrom aioclock.custom_types import Triggers\"\"\"\nfrom aioclock.group import Group, Task\"\"\"\nfrom aioclock.provider import get_provider\"\"\"\nfrom aioclock.triggers import BaseTrigger\"\"\"\nfrom aioclock.utils import flatten_chain\"\"\"\n\"\"\"\nT = TypeVar('T')\"\"\"\nP = ParamSpec('P')\"\"\"\n\"\"\"\nclass AioClock:\"\"\"\n    \"\"\"\n    AioClock is the main class that will be used to run the tasks.\"\"\"\n    It will be responsible for running the tasks in the right order.\"\"\"\n    \"\"\"\n    Example:\"\"\"\n        \"\"\"python\"\"\"\n        from aioclock import AioClock, Once\"\"\"\n        import asyncio\"\"\"\n\"\"\"\n        app = AioClock()\"\"\"\n        @app.task(trigger=Once())\"\"\"\n        async def main():\"\"\"\n            print('Hello World')\"\"\"\n        \"\"\"\n    \"\"\"\n    def __init__(self, limiter=None):\"\"\"\n        \"\"\"\n        Initialize AioClock instance.\"\"\"\n        Parameters:\"\"\"\n            limiter: Optional[Any]: An optional limiter to limit the capacity.\"\"\"\n        \"\"\"\n        self._groups: list[Group] = []\"\"\"\n        self._app_tasks: list[Task] = []\"\"\"\n\"\"\"\n    @property\"\"\"\n    def dependencies(self) -> Any:\"\"\"\n        \"\"\"\n        Dependencies provider that will be used to inject dependencies in tasks.\"\"\"\n        return get_provider()\"\"\"\n\"\"\"\n    def override_dependencies(self, original: Callable[..., Any], override: Callable[..., Any]) -> None:\"\"\"\n        \"\"\"\n        Override a dependency with a new one.\"\"\"\n        self.dependencies.override(original, override)\"\"\"\n\"\"\"\n    def include_group(self, group: Group) -> None:\"\"\"\n        \"\"\"\n        Include a group of tasks that will be run by AioClock.\"\"\"\n        self._groups.append(group)\"\"\"\n        return None\"\"\"\n\"\"\"\n    def task(self, *, trigger: BaseTrigger):\"\"\"\n        \"\"\"\n        Decorator to add a task to the AioClock instance.\"\"\"\n\"\"\"\n        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:\"\"\"\n            @wraps(func)\"\"\"\n            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:\"\"\"\n                return await func(*args, **kwargs)\"\"\"\n\"\"\"\n            self._app_tasks.append(\"\"\"\n                Task(\"\"\"\n                    func=inject(wrapper, dependency_overrides_provider=get_provider()),\"\"\"\n                    trigger=trigger,\"\"\"\n                )\"\"\"\n            )\"\"\"\n            return wrapper\"\"\"\n\"\"\"\n        return decorator\"\"\"\n\"\"\"\n    @property\"\"\"\n    def _tasks(self) -> list[Task]:\"\"\"\n        result = flatten_chain([group._tasks for group in self._groups])\"\"\"\n        return result\"\"\"\n\"\"\"\n    def _get_shutdown_task(self) -> list[Task]:\"\"\"\n        return [task for task in self._tasks if task.trigger.type_ == Triggers.ON_SHUT_DOWN]\"\"\"\n\"\"\"\n    def _get_startup_task(self) -> list[Task]:\"\"\"\n        return [task for task in self._tasks if task.trigger.type_ == Triggers.ON_START_UP]\"\"\"\n\"\"\"\n    def _get_tasks(self, exclude_type: Union[set[Triggers], None] = None) -> list[Task]:\"\"\"\n        exclude_type = \"\"\"\n            exclude_type \"\"\"\n            if exclude_type is not None \"\"\"\n            else {Triggers.ON_START_UP, Triggers.ON_SHUT_DOWN}\"\"\"\n\"\"\"\n        return [task for task in self._tasks if task.trigger.type_ not in exclude_type]\"\"\"\n\"\"\"\n    async def serve(self) -> None:\"\"\"\n        \"\"\"\n        Serves AioClock\"\"\"\n        Run the tasks in the right order.\"\"\"\n        First, run the startup tasks, then run the tasks, and finally run the shutdown tasks.\"\"\"\n        \"\"\"\n        self.include_group(Group(tasks=self._app_tasks))\"\"\"\n        try:\"\"\"\n            await asyncio.gather(\n                *(task.run() for task in self._get_startup_task()), return_exceptions=False\"\"\"\n            )\n\"\"\"\n            await asyncio.gather(\n                *(group.run() for group in self._get_tasks()), return_exceptions=False\"\"\"\n            )\n        finally:\"\"\"\n            shutdown_tasks = self._get_shutdown_task()\"\"\"\n            await asyncio.gather(*(task.run() for task in shutdown_tasks), return_exceptions=False)\"\"\"\n