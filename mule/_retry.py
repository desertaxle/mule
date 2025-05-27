from functools import partial, update_wrapper
from typing import Callable, Generic, TypeVar, cast, overload
from typing_extensions import ParamSpec

from mule.stop_conditions import StopCondition
from mule._attempts import AttemptGenerator


P = ParamSpec("P")
R = TypeVar("R")


class Retriable(Generic[P, R]):
    """
    A callable that retries a function until a stop condition is met.

    In most cases, you should use the `@retry` decorator instead of instantiating this class directly.

    Args:
        __fn: The function to retry on failure.
        until: A `StopCondition` that determines when to stop retrying the provided function.
    """

    def __init__(self, __fn: Callable[P, R], *, until: StopCondition | None = None):
        self.fn = __fn
        update_wrapper(self, __fn)
        self.attempting: AttemptGenerator = AttemptGenerator(until=until)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        for attempt in self.attempting:
            with attempt:
                return self.fn(*args, **kwargs)

        raise RuntimeError(
            "Failed to make a single attempt with the given stop condition"
        )


@overload
def retry(
    __fn: None = None, *, until: StopCondition | None = None
) -> Callable[[Callable[P, R]], Retriable[P, R]]: ...


@overload
def retry(
    __fn: Callable[P, R], *, until: StopCondition | None = None
) -> Retriable[P, R]: ...


def retry(
    __fn: Callable[P, R] | None = None, *, until: StopCondition | None = None
) -> Retriable[P, R] | Callable[[Callable[P, R]], Retriable[P, R]]:
    """
    A function decorator that retries a function until a stop condition is met.

    Args:
        until: A `StopCondition` that determines when to stop retrying the provided function.

    Example:
        Retry a function until 3 attempts have been made.
        ```python
        from mule.retry import retry
        from mule.stop_conditions import AttemptsExhausted

        @retry(until=AttemptsExhausted(3))
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
            partial(retry, until=until),
        )
    else:
        return Retriable(__fn, until=until)
