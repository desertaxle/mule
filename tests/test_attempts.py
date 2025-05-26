import pytest

from mule import attempting
from mule._attempts import AttemptGenerator
from mule.stop_conditions import AttemptsExhausted, NoException


class TestAttemptGenerator:
    def test_default_stop_condition(self):
        generator = AttemptGenerator()
        assert generator.stop_condition == NoException()


class TestAttempting:
    def test_retry_context_with_eventual_success(self):
        attempts = 0
        result = None
        for attempt in attempting(until=AttemptsExhausted(3)):
            with attempt:
                attempts += 1
                if attempts < 2:
                    raise Exception("Test exception")
                else:
                    result = "Success"

        assert result is not None
        assert attempts == 2

    def test_retry_context_with_failure(self):
        attempts = 0
        with pytest.raises(Exception):
            for attempt in attempting(until=AttemptsExhausted(3)):
                with attempt:
                    attempts += 1
                    raise Exception("Test exception")

        assert attempts == 3
