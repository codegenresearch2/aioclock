import asyncio\nimport sys\nfrom functools import wraps\nfrom typing import Awaitable, Callable, TypeVar, Union, Optional\nif sys.version_info < (3, 10):\n    from typing_extensions import ParamSpec\nelse:\n    from typing import ParamSpec\nfrom fast_depends import inject\nfrom aioclock.provider import get_provider\nfrom aioclock.task import Task\nfrom aioclock.triggers import BaseTrigger\nfrom anyio import CapacityLimiter\nfrom asyncer import asyncify\n\nT = TypeVar("T")\nP = ParamSpec("P")\n\nclass Group:\n    def __init__(self, limiter: Optional[CapacityLimiter] = None):\n        """ Group of tasks that will be run together. \"\n        Best use case is to have a good modularity and separation of concerns. \"\n        For example, you can have a group of tasks that are responsible for sending emails. \"\n        And another group of tasks that are responsible for sending notifications. \"\n        \"\n        Parameters:\"\n            limiter: An optional limiter to limit the number of concurrent tasks. \"\n        """\n        self._tasks: list[Task] = []\n        self._limiter = limiter\n    \n    def task(self, *, trigger: BaseTrigger):\n        """ Function used to decorate tasks, to be registered inside AioClock. \"\n        \"\n        Parameters:\"\n            trigger: The trigger that will be used to run the function. \"\n        """\n        def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:\n            @wraps(func)\n            async def wrapped_function(*args: P.args, **kwargs: P.kwargs) -> T:\n                return await func(*args, **kwargs)\n            self._tasks.append(\n                Task(\n                    func=inject(wrapped_function, dependency_overrides_provider=get_provider()),\n                    trigger=trigger,\n                )\n           )\n            return wrapped_function\n        return decorator\n    \n    async def _run(self):\n        """ Just for purpose of being able to run all task in group \"\n        Private method, should not be used outside of the library \"\n        """\n        await asyncio.gather(\n            *(task.run() for task in self._tasks),\n            return_exceptions=False,\n        )\n