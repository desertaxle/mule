from __future__ import annotations

import abc

from mule._attempts import AttemptContext


class Until(abc.ABC):
    """
    A protocol that defines a stopping condition for an attempting generator.
    """

    @abc.abstractmethod
    def is_condition_met(self, context: AttemptContext | None) -> bool:
        """
        Checks if execution should stop.

        Args:
            context: The current attempt context.

        Returns:
            True if the stopping condition is met, False otherwise.
        """
        ...  # pragma: no cover

    def __and__(self, other: Until) -> Until:
        return CompositeUntilAll(self, other)

    def __or__(self, other: Until) -> Until:
        return CompositeUntilAny(self, other)


class NoException(Until):
    """
    An Until implementation that stops if no exception is raised in the attempt context.
    """

    def is_condition_met(self, context: AttemptContext | None) -> bool:
        if context is None:
            return False
        return context.exception is None


class ExceptionMatches(Until):
    """
    An Until implementation that stops if the exception matches the given type.
    """

    def __init__(self, exception_type: type[BaseException]):
        self.exception_type = exception_type

    def is_condition_met(self, context: AttemptContext | None) -> bool:
        if context is None:
            return False
        return isinstance(context.exception, self.exception_type)


class AttemptsExhausted(Until):
    """
    An Until implementation that stops after a fixed number of attempts.

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
        return context.attempt >= self.max_attempts


class CompositeUntilAll(Until):
    """
    An Until implementation that stops if all of the given Until instances are met.
    """

    def __init__(self, *until: Until):
        self.until: tuple[Until, ...] = until

    def is_condition_met(self, context: AttemptContext | None) -> bool:
        return all(until.is_condition_met(context) for until in self.until)


class CompositeUntilAny(Until):
    """
    An Until implementation that stops if any of the given Until instances are met.
    """

    def __init__(self, *until: Until):
        self.until: tuple[Until, ...] = until

    def is_condition_met(self, context: AttemptContext | None) -> bool:
        return any(until.is_condition_met(context) for until in self.until)


def attempts_exhausted(max_attempts: int) -> Until:
    """
    A convenience function that returns an Until implementation keeps attempting if there is an exception,
    but stops after a fixed number of attempts.
    """
    return AttemptsExhausted(max_attempts) | NoException()
