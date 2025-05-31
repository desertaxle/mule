from __future__ import annotations
import asyncio
import datetime
from types import TracebackType
from typing import TYPE_CHECKING

from mule.stop_conditions import NoException, StopCondition
from .dataclasses import AttemptState

if TYPE_CHECKING:
    from .protocols import WaitTimeProvider  # pragma: no cover


class AsyncAttemptGenerator:
    """
    An async generator that yields attempt contexts until a stopping condition is met.

    The stopping condition is defined by the `StopCondition` protocol.
    """

    def __init__(
        self,
        until: "StopCondition | None" = None,
        wait: "datetime.timedelta | int | float | None | WaitTimeProvider" = None,
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
        self._attempts: list[AsyncAttemptContext] = []

    @property
    def last_attempt(self) -> AsyncAttemptContext | None:
        """
        Get the last attempt context.
        """
        if not self._attempts:
            return None
        return self._attempts[-1]

    def get_next_attempt(self) -> AsyncAttemptContext:
        """
        Get the next attempt context.
        """
        if not self.last_attempt:
            next_attempt = AsyncAttemptContext(1)
            self._attempts.append(next_attempt)
            return next_attempt
        else:
            next_attempt = AsyncAttemptContext(self.last_attempt.attempt + 1)
            self._attempts.append(next_attempt)
            return next_attempt

    def __aiter__(self) -> AsyncAttemptGenerator:
        return self

    async def _wait_for_next_attempt(self, attempt: "AttemptState") -> None:
        """
        Wait for the appropriate amount of time before the next attempt, if needed.

        Args:
            attempt: The current AttemptContext.
        """
        if attempt.attempt > 1 and self.wait:
            wait_time = self.wait
            if callable(wait_time):
                wait_time = wait_time(
                    self.last_attempt.to_attempt_state() if self.last_attempt else None,
                    attempt,
                )
            if wait_time is not None:
                if isinstance(wait_time, datetime.timedelta):
                    await asyncio.sleep(wait_time.total_seconds())
                else:
                    await asyncio.sleep(float(wait_time))

    async def __anext__(self) -> AsyncAttemptContext:
        if self.stop_condition.is_met(
            self.last_attempt.to_attempt_state() if self.last_attempt else None
        ):
            if self.last_attempt and (last_exception := self.last_attempt.exception):
                raise last_exception
            else:
                raise StopAsyncIteration

        attempt = self.get_next_attempt()
        await self._wait_for_next_attempt(attempt.to_attempt_state())
        return attempt


class AsyncAttemptContext:
    """
    An async context manager that represents an attempt.

    The attempt context is used to track the attempt number and the exception that occurred.
    """

    def __init__(self, attempt: int):
        self.attempt = attempt
        self.exception: BaseException | None = None

    async def __aenter__(self) -> AsyncAttemptContext:
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> bool | None:
        if _exc_value:
            self.exception = _exc_value
            return True

    def to_attempt_state(self) -> AttemptState:
        return AttemptState(
            attempt=self.attempt,
            exception=self.exception,
        )


attempting_async = AsyncAttemptGenerator
