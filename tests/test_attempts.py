import datetime
from unittest.mock import MagicMock
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


class TestWait:
    @pytest.fixture
    def mock_sleep(self, monkeypatch: pytest.MonkeyPatch):
        mock_sleep = MagicMock()
        monkeypatch.setattr("time.sleep", mock_sleep)
        return mock_sleep

    @pytest.mark.parametrize("wait", [5, datetime.timedelta(seconds=5), 5.0])
    def test_wait(self, wait: int | datetime.timedelta, mock_sleep: MagicMock):
        attempts = 0
        for attempt in attempting(until=AttemptsExhausted(3), wait=wait):
            with attempt:
                attempts += 1
                if attempts < 2:
                    raise Exception("Test exception")

        if isinstance(wait, datetime.timedelta):
            mock_sleep.assert_called_once_with(wait.total_seconds())
        else:
            mock_sleep.assert_called_once_with(wait)
