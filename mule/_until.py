from __future__ import annotations

from typing import Protocol

from mule._attempts import AttemptContext


class Until(Protocol):
    """
    A protocol that defines a stopping condition for an attempting generator.
    """

    def is_condition_met(self, context: AttemptContext | None) -> bool:
        """
        Checks if execution should stop.

        Args:
            context: The current attempt context.

        Returns:
            True if the stopping condition is met, False otherwise.
        """
        ...  # pragma: no cover


class AttemptsExhausted(Until):
    """
    A Until implementation that stops after a fixed number of attempts.

    Attributes:
        max_attempts: The maximum number of attempts. Execution will stop after
            this many failed attempts.
    """

    def __init__(self, max_attempts: int):
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than 0")
        self.max_attempts = max_attempts

    def is_condition_met(self, context: AttemptContext | None) -> bool:
        if context is None:
            return False
        if context and context.exception is None:
            return True
        return context.attempt >= self.max_attempts
