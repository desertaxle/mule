from __future__ import annotations
import datetime
import time
from types import TracebackType
from typing_extensions import Protocol

from mule.stop_conditions import NoException, StopCondition


class WaitTimeProvider(Protocol):
    """
    Protocol for callables that produce a wait time given the previous and next AttemptContext.

    Args:
        prev: The previous AttemptContext, or None if this is the first attempt.
        next: The next AttemptContext (the one about to be run).

    Returns:
        The wait time as a timedelta, seconds (int/float), or None.
    """

    def __call__(
        self, prev: "AttemptContext | None", next: "AttemptContext"
    ) -> datetime.timedelta | int | float | None: ...


class AttemptGenerator:
    """
    A generator that yields attempt contexts until a stopping condition is met.

    The stopping condition is defined by the `StopCondition` protocol.
    """

    def __init__(
        self,
        until: "StopCondition | None" = None,
        wait: datetime.timedelta | int | float | None | WaitTimeProvider = None,
    ):
        """
        Initialize the AttemptGenerator.

        Args:
            until: The stop condition for attempts.
            wait: The wait time between attempts. Can be a timedelta, seconds (int/float),
                or a WaitTimeProvider callable that takes an AttemptContext and returns a timedelta, seconds, or None.
        """
        if until is None:
            self.stop_condition = NoException()
        else:
            self.stop_condition: "StopCondition" = until | NoException()
        self.wait = wait
        self._attempts: list[AttemptContext] = []

    @property
    def last_attempt(self) -> AttemptContext | None:
        """
        Get the last attempt context.
        """
        if not self._attempts:
            return None
        return self._attempts[-1]

    def get_next_attempt(self) -> AttemptContext:
        """
        Get the next attempt context.
        """
        if not self.last_attempt:
            next_attempt = AttemptContext(1)
            self._attempts.append(next_attempt)
            return next_attempt
        else:
            next_attempt = AttemptContext(self.last_attempt.attempt + 1)
            self._attempts.append(next_attempt)
            return next_attempt

    def __iter__(self) -> AttemptGenerator:
        return self

    def _wait_for_next_attempt(self, attempt: "AttemptContext") -> None:
        """
        Wait for the appropriate amount of time before the next attempt, if needed.

        Args:
            attempt: The current AttemptContext.
        """
        if attempt.attempt > 1 and self.wait:
            wait_time = self.wait
            if callable(wait_time):
                wait_time = wait_time(self.last_attempt, attempt)
            if wait_time is not None:
                if isinstance(wait_time, datetime.timedelta):
                    time.sleep(wait_time.total_seconds())
                else:
                    time.sleep(float(wait_time))

    def __next__(self) -> AttemptContext:
        if self.stop_condition.is_met(self.last_attempt):
            if self.last_attempt and (last_exception := self.last_attempt.exception):
                raise last_exception
            else:
                raise StopIteration

        attempt = self.get_next_attempt()
        self._wait_for_next_attempt(attempt)
        return attempt


class AttemptContext:
    """
    A context manager that represents an attempt.

    The attempt context is used to track the attempt number and the exception that occurred.
    """

    def __init__(self, attempt: int):
        self.attempt = attempt
        self.exception: BaseException | None = None

    def __enter__(self) -> AttemptContext:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> bool | None:
        if _exc_value:
            self.exception = _exc_value
            return True


attempting = AttemptGenerator
