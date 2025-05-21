from __future__ import annotations
from types import TracebackType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mule._until import Until  # pragma: no cover


class AttemptGenerator:
    """
    A generator that yields attempt contexts until a stopping condition is met.

    The stopping condition is defined by the `Until` protocol.
    """

    def __init__(self, until: "Until"):
        self.until: "Until" = until
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

    def __next__(self) -> AttemptContext:
        if self.until.is_condition_met(self.last_attempt):
            if self.last_attempt and (last_exception := self.last_attempt.exception):
                raise last_exception
            else:
                raise StopIteration

        return self.get_next_attempt()


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
