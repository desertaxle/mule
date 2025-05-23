import pytest

from mule._until import (
    CompositeUntilAny,
    AttemptsExhausted,
    ExceptionMatches,
    NoException,
    CompositeUntilAll,
)
from mule._attempts import AttemptContext


class TestAttemptsExhausted:
    def test_attempts_exhausted(self):
        until = AttemptsExhausted(3)
        assert until.is_condition_met(None) is False

        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is False

        context = AttemptContext(attempt=2)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is False

        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is True

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError):
            AttemptsExhausted(0)

        with pytest.raises(ValueError):
            AttemptsExhausted(-1)


class TestNoException:
    def test_no_exception(self):
        until = NoException()
        assert until.is_condition_met(None) is False

        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is False


class TestExceptionMatches:
    def test_exception_matches(self):
        until = ExceptionMatches(RuntimeError)
        assert until.is_condition_met(None) is False

        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is True


class TestCompositeUntilAll:
    def test_all_conditions_met(self):
        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        until = CompositeUntilAll(AttemptsExhausted(3), NoException())
        assert until.is_condition_met(context) is False  # NoException not met
        context.exception = None
        assert until.is_condition_met(context) is True  # Both met

    def test_not_all_conditions_met(self):
        context = AttemptContext(attempt=2)
        context.exception = RuntimeError()
        until = CompositeUntilAll(AttemptsExhausted(3), NoException())
        assert until.is_condition_met(context) is False

    def test_creation_via_and(self):
        # A bit nonsensical, but we'll test it anyway.
        until = AttemptsExhausted(3) & NoException()
        assert isinstance(until, CompositeUntilAll)

        # No exception, but the max attempts is not reached, so it should be false.
        context = AttemptContext(attempt=1)
        assert until.is_condition_met(context) is False

        # Max attempts is reached, but there is an exception, so it should be false.
        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is False

        # No exception and the max attempts is reached, so it should be true.
        context = AttemptContext(attempt=3)
        context.exception = None
        assert until.is_condition_met(context) is True


class TestCompositeUntilAny:
    def test_any_condition_met(self):
        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        until = CompositeUntilAny(AttemptsExhausted(3), NoException())
        assert until.is_condition_met(context) is True  # AttemptsExhausted met
        context = AttemptContext(attempt=1)
        context.exception = None
        assert until.is_condition_met(context) is True  # NoException met

    def test_no_conditions_met(self):
        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        until = CompositeUntilAny(AttemptsExhausted(3), NoException())
        assert until.is_condition_met(context) is False

    def test_creation_via_or(self):
        until = AttemptsExhausted(3) | NoException()
        assert isinstance(until, CompositeUntilAny)

        # No exception, so it should be true.
        context = AttemptContext(attempt=1)
        assert until.is_condition_met(context) is True

        # Max attempts is reached, so it should be true.
        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is True


class TestComplexUntilCombinations:
    def test_nested_and_or(self):
        # (AttemptsExhausted(3) & NoException()) | ExceptionMatches(ValueError)
        until = (AttemptsExhausted(3) & NoException()) | ExceptionMatches(ValueError)
        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        assert (
            until.is_condition_met(context) is False
        )  # Neither AND nor ExceptionMatches(ValueError) met

        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        assert (
            until.is_condition_met(context) is False
        )  # AND not met, ExceptionMatches(ValueError) not met

        context.exception = None
        assert until.is_condition_met(context) is True  # AND met

        context = AttemptContext(attempt=1)
        context.exception = ValueError()
        assert (
            until.is_condition_met(context) is True
        )  # ExceptionMatches(ValueError) met

    def test_nested_or_and(self):
        # (AttemptsExhausted(3) | NoException()) & ExceptionMatches(ValueError)
        until = (AttemptsExhausted(3) | NoException()) & ExceptionMatches(ValueError)
        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        assert (
            until.is_condition_met(context) is False
        )  # ExceptionMatches(ValueError) not met

        context.exception = ValueError()
        assert (
            until.is_condition_met(context) is False
        )  # ExceptionMatches(ValueError) met, NoException not met

        context = AttemptContext(attempt=3)
        context.exception = ValueError()
        assert (
            until.is_condition_met(context) is True
        )  # AttemptsExhausted(3) met, ExceptionMatches(ValueError) met

    def test_multiple_and_or(self):
        # AttemptsExhausted(3) & NoException() & ExceptionMatches(ValueError)
        until = AttemptsExhausted(3) & NoException() & ExceptionMatches(ValueError)
        context = AttemptContext(attempt=3)
        context.exception = ValueError()
        assert until.is_condition_met(context) is False  # NoException not met

        context.exception = None
        assert (
            until.is_condition_met(context) is False
        )  # ExceptionMatches(ValueError) not met

        # Only if all are met
        # This is not possible, but test for completeness

    def test_multiple_or(self):
        # AttemptsExhausted(3) | NoException() | ExceptionMatches(ValueError)
        until = AttemptsExhausted(3) | NoException() | ExceptionMatches(ValueError)
        context = AttemptContext(attempt=1)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is False

        context = AttemptContext(attempt=3)
        context.exception = RuntimeError()
        assert until.is_condition_met(context) is True  # AttemptsExhausted(3) met

        context = AttemptContext(attempt=1)
        context.exception = None
        assert until.is_condition_met(context) is True  # NoException met

        context = AttemptContext(attempt=1)
        context.exception = ValueError()
        assert (
            until.is_condition_met(context) is True
        )  # ExceptionMatches(ValueError) met
