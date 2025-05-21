import pytest

from mule import AttemptsExhausted
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
