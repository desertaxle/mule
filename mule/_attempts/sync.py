from __future__ import annotations

import asyncio
import datetime
import logging
import time
from inspect import iscoroutinefunction
from types import TracebackType
from typing import TYPE_CHECKING, Any, Literal, Sequence

from mule._attempts.protocols import HookType
from mule.stop_conditions import NoException, StopCondition

from .dataclasses import AttemptState, Phase

if TYPE_CHECKING:
    from .protocols import (
        AsyncAttemptHook,
        AttemptHook,
        WaitTimeProvider,
    )  # pragma: no cover

_logger = logging.getLogger("mule")


class AttemptGenerator:
    """
    A generator that yields attempt contexts until a stopping condition is met.

    The stopping condition is defined by the `StopCondition` protocol.
    """

    def __init__(
        self,
        *,
        until: "StopCondition | None" = None,
        wait: "datetime.timedelta | int | float | None | WaitTimeProvider" = None,
        before_attempt: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
        on_success: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
        on_failure: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
        before_wait: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
        after_wait: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
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
        self.before_attempt = before_attempt
        self.on_success = on_success
        self.on_failure = on_failure
        self.before_wait = before_wait
        self.after_wait = after_wait

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
            next_attempt = AttemptContext(
                attempt=1,
                before_attempt=self.before_attempt,
                on_success=self.on_success,
                on_failure=self.on_failure,
            )
            self._attempts.append(next_attempt)
            return next_attempt
        else:
            next_attempt = AttemptContext(
                attempt=self.last_attempt.attempt + 1,
                before_attempt=self.before_attempt,
                on_success=self.on_success,
                on_failure=self.on_failure,
            )
            self._attempts.append(next_attempt)
            return next_attempt

    def __iter__(self) -> AttemptGenerator:
        return self

    def _call_hooks(
        self, attempt: AttemptContext, hooks_type: Literal["before_wait", "after_wait"]
    ) -> None:
        default_hooks: Sequence[AttemptHook] = tuple()
        hooks: Sequence[AttemptHook] = getattr(self, hooks_type, default_hooks)
        async_hooks: list[AsyncAttemptHook] = []
        for hook in hooks:
            if iscoroutinefunction(hook):
                async_hooks.append(hook)
            else:
                try:
                    state = attempt.to_attempt_state()
                    hook(state=state)
                except Exception as e:
                    _logger.error(
                        f"Error calling {hooks_type} hook {hook.__name__}", exc_info=e
                    )
        if async_hooks:
            _call_async_hooks(async_hooks, attempt.to_attempt_state(), hooks_type)

    def _wait_for_next_attempt(self, attempt: "AttemptContext") -> None:
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
                    attempt.to_attempt_state(),
                )
            if wait_time is not None:
                wait_seconds = (
                    wait_time.total_seconds()
                    if isinstance(wait_time, datetime.timedelta)
                    else float(wait_time)
                )
                attempt.wait_seconds = wait_seconds
                attempt.phase = Phase.WAITING
                self._call_hooks(attempt, "before_wait")
                time.sleep(wait_seconds)
                attempt.phase = Phase.PENDING
                attempt.wait_seconds = None
                self._call_hooks(attempt, "after_wait")

    def __next__(self) -> AttemptContext:
        if self.stop_condition.is_met(
            self.last_attempt.to_attempt_state() if self.last_attempt else None
        ):
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

    The attempt context is used to track the attempt number, the exception that occurred,
    the result of the attempt, and the number of seconds waited after the attempt.
    """

    def __init__(
        self,
        attempt: int,
        before_attempt: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
        on_success: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
        on_failure: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple(),
    ):
        self.attempt = attempt
        self.exception: BaseException | None = None
        self.result: Any = ...  # Ellipsis is used as a sentinel to indicate that a result has not been set yet.
        self.wait_seconds: float | None = None
        self.phase: Phase = Phase.PENDING
        self.before_attempt = before_attempt
        self.on_success = on_success
        self.on_failure = on_failure

    def _call_hooks(
        self, hooks_type: Literal["before_attempt", "on_success", "on_failure"]
    ) -> None:
        default_hooks: "Sequence[AttemptHook | AsyncAttemptHook]" = tuple()
        hooks: "Sequence[AttemptHook | AsyncAttemptHook]" = getattr(
            self, hooks_type, default_hooks
        )
        async_hooks: list[AsyncAttemptHook] = []
        for hook in hooks:
            if iscoroutinefunction(hook):
                async_hooks.append(hook)
            else:
                try:
                    state = self.to_attempt_state()
                    hook(state=state)
                except Exception as e:
                    _logger.error(
                        f"Error calling {hooks_type} hook {hook.__name__}", exc_info=e
                    )
        if async_hooks:
            _call_async_hooks(async_hooks, self.to_attempt_state(), hooks_type)

    def __enter__(self) -> AttemptContext:
        self._call_hooks("before_attempt")
        self.phase = Phase.RUNNING
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> bool | None:
        if _exc_value:
            self.exception = _exc_value
            self.phase = Phase.FAILED
            self._call_hooks("on_failure")
        else:
            self.phase = Phase.SUCCEEDED
            self._call_hooks("on_success")
        return True

    def to_attempt_state(self) -> AttemptState:
        return AttemptState(
            attempt=self.attempt,
            exception=self.exception,
            result=self.result,
            wait_seconds=self.wait_seconds,
            phase=self.phase,
        )


attempting = AttemptGenerator


def _call_async_hooks(
    hooks: Sequence[AsyncAttemptHook],
    state: AttemptState,
    hook_type: HookType,
) -> None:
    async def _call_hook(hook: AsyncAttemptHook) -> None:
        try:
            await hook(state=state)
        except Exception as e:
            _logger.error(f"Error calling {hook_type} hook {hook.__name__}", exc_info=e)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio.gather(*[_call_hook(hook) for hook in hooks]))
