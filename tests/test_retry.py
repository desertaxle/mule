from __future__ import annotations

import pytest
from mule._attempts import AttemptContext
from mule._retry import retry, Retriable
from mule.stop_conditions import AttemptsExhausted, StopCondition


def always_succeeds(x: int) -> int:
    return x * 2


def sometimes_fails(x: int) -> int:
    """
    Sometimes fails with a ValueError.
    """
    if x < 0:
        raise ValueError("Negative!")
    return x


class TestRetriable:
    def test_retriable_success(self):
        r = Retriable(always_succeeds, until=AttemptsExhausted(3))
        assert r(5) == 10

    def test_retriable_failure(self):
        r = Retriable(
            lambda: (_ for _ in ()).throw(ValueError()), until=AttemptsExhausted(2)
        )
        with pytest.raises(ValueError):
            r()

    def test_retriable_eventual_success(self):
        attempts = 0

        def fn(x: int) -> int:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise Exception("fail")
            return x

        r = Retriable(fn, until=AttemptsExhausted(3))
        assert r(42) == 42
        assert attempts == 2

    def test_retriable_wraps_callable(self):
        r = Retriable(sometimes_fails, until=AttemptsExhausted(3))
        assert getattr(r, "__wrapped__", None) is sometimes_fails
        assert getattr(r, "__name__", None) == "sometimes_fails"
        assert getattr(r, "__doc__", None) == sometimes_fails.__doc__


class TestRetryDecorator:
    def test_retry_decorator_success(self):
        @retry(until=AttemptsExhausted(2))
        def f(x: int) -> int:
            return x + 1

        assert f(2) == 3

    def test_retry_decorator_eventual_success(self):
        attempts = 0

        @retry(until=AttemptsExhausted(3))
        def f(x: int) -> int:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise Exception("fail")
            return x

        assert f(7) == 7
        assert attempts == 2

    def test_retry_decorator_no_until(self):
        @retry
        def f(x: int) -> int:
            return x * 3

        assert f(3) == 9

    def test_retry_with_invalid_stop_condition(self):
        class NeverAttempt(StopCondition):
            def is_met(self, context: AttemptContext | None) -> bool:
                return True

        @retry(until=NeverAttempt())
        def f(x: int) -> int:
            return x * 3

        with pytest.raises(
            RuntimeError,
            match="Failed to make a single attempt with the given stop condition",
        ):
            f(3)
