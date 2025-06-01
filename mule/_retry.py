from __future__ import annotations

from asyncio import iscoroutinefunction
import datetime
from functools import partial, update_wrapper
from typing import Awaitable, Callable, Generic, TypeVar, cast, overload
from typing_extensions import ParamSpec

from mule._attempts.aio import AsyncAttemptGenerator
from mule.stop_conditions import StopCondition
from mule._attempts import AttemptGenerator, WaitTimeProvider


P = ParamSpec("P")
R = TypeVar("R")


class Retriable(Generic[P, R]):
    """
    A callable that retries a function until a stop condition is met.

    In most cases, you should use the `@retry` decorator instead of instantiating this class directly.

    Args:
        __fn: The function to retry on failure.
        until: A `StopCondition` that determines when to stop retrying the provided function.
        wait: A `datetime.timedelta`, a number of seconds, or a callable that takes an AttemptContext and returns a timedelta, seconds, or None.
    """

    def __init__(
        self,
        __fn: Callable[P, R],
        *,
        until: StopCondition | None = None,
        wait: datetime.timedelta | int | float | None | WaitTimeProvider = None,
    ):
        self.fn = __fn
        update_wrapper(self, __fn)
        self.attempting: AttemptGenerator = AttemptGenerator(until=until, wait=wait)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        for attempt in self.attempting:
            with attempt:
                return self.fn(*args, **kwargs)

        raise RuntimeError(
            "Failed to make a single attempt with the given stop condition"
        )


class AsyncRetriable(Generic[P, R]):
    """
    A callable that retries a function until a stop condition is met.
    """

    def __init__(
        self,
        __fn: Callable[P, Awaitable[R]],
        *,
        until: StopCondition | None = None,
        wait: datetime.timedelta | int | float | None | WaitTimeProvider = None,
    ):
        self.fn = __fn
        update_wrapper(self, __fn)
        self.attempting: AsyncAttemptGenerator = AsyncAttemptGenerator(
            until=until, wait=wait
        )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
        async def _call():
            async for attempt in self.attempting:
                async with attempt:
                    return await self.fn(*args, **kwargs)

            raise RuntimeError(
                "Failed to make a single attempt with the given stop condition"
            )

        return _call()


@overload
def retry(
    __fn: None = None,
    *,
    until: StopCondition | None = None,
    wait: datetime.timedelta | int | float | None | WaitTimeProvider = None,
) -> Callable[[Callable[P, R]], Retriable[P, R]]: ...


@overload
def retry(
    __fn: Callable[P, R],
    *,
    until: StopCondition | None = None,
    wait: datetime.timedelta | int | float | None | WaitTimeProvider = None,
) -> Retriable[P, R]: ...


def retry(
    __fn: Callable[P, R] | None = None,
    *,
    until: StopCondition | None = None,
    wait: datetime.timedelta | int | float | None | WaitTimeProvider = None,
) -> Retriable[P, R] | Callable[[Callable[P, R]], Retriable[P, R]]:
    """
    A function decorator that retries a function until a stop condition is met.

    Args:
        until: A `StopCondition` that determines when to stop retrying the provided function.
        wait: A `datetime.timedelta`, a number of seconds, or a callable that takes an AttemptContext and returns a timedelta, seconds, or None.

    Example:
        Retry a function until 3 attempts have been made:
        ```python
        from mule import retry
        from mule.stop_conditions import AttemptsExhausted

        @retry(until=AttemptsExhausted(3))
        def f(x: int) -> int:
            return x * 3
        ```

        Retry a function until 3 attempts have been made, waiting 5 seconds between attempts:
        ```python
        from mule import retry
        from mule.stop_conditions import AttemptsExhausted

        @retry(until=AttemptsExhausted(3), wait=5)
        def f(x: int) -> int:
            return x * 3
        ```

        Retry a function with exponential backoff (doubling wait each time, up to 60s):
        ```python
        from mule import retry
        from mule.stop_conditions import AttemptsExhausted
        import datetime

        def exp_backoff(ctx):
            return min(2 ** (ctx.attempt - 1), 60)

        @retry(until=AttemptsExhausted(5), wait=exp_backoff)
        def f(x: int) -> int:
            return x * 3
        ```

        Retry a function as long as the raised exception is not a `ValueError`:
        ```python
        from mule import retry
        from mule.stop_conditions import ExceptionMatches

        @retry(until=~ExceptionMatches(ValueError))
        def f(x: int) -> int:
            return x * 3
        ```
    """
    if __fn is None:
        return cast(
            Callable[
                [Callable[P, R]],
                Retriable[P, R],
            ],
            partial(retry, until=until, wait=wait),
        )
    elif iscoroutinefunction(__fn):
        return AsyncRetriable(__fn, until=until, wait=wait)
    else:
        return Retriable(__fn, until=until, wait=wait)
