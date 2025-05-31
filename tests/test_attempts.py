from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest

from mule import attempting, attempting_async
from mule._attempts import AttemptGenerator, AsyncAttemptGenerator
from mule._attempts.dataclasses import AttemptState
from mule.stop_conditions import AttemptsExhausted, NoException


class TestAttemptGenerator:
    def test_default_stop_condition(self):
        generator = AttemptGenerator()
        assert generator.stop_condition == NoException()


class TestAsyncAttemptGenerator:
    def test_default_stop_condition(self):
        generator = AsyncAttemptGenerator()
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


class TestAsyncAttempting:
    async def test_retry_context_with_eventual_success(self):
        attempts = 0
        result = None
        async for attempt in attempting_async(until=AttemptsExhausted(3)):
            async with attempt:
                attempts += 1
                if attempts < 2:
                    raise Exception("Test exception")
                else:
                    result = "Success"

        assert result is not None
        assert attempts == 2

    async def test_retry_context_with_failure(self):
        attempts = 0
        with pytest.raises(Exception):
            async for attempt in attempting_async(until=AttemptsExhausted(3)):
                async with attempt:
                    attempts += 1
                    raise Exception("Test exception")

        assert attempts == 3


class TestWait:
    @pytest.fixture
    def mock_sleep(self, monkeypatch: pytest.MonkeyPatch):
        mock_sleep = MagicMock()
        monkeypatch.setattr("time.sleep", mock_sleep)
        return mock_sleep

    @pytest.mark.parametrize("wait", [5, datetime.timedelta(minutes=5), 5.0])
    def test_wait(self, wait: int | float | datetime.timedelta, mock_sleep: MagicMock):
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

    def test_wait_with_exponential_backoff_callable(self, mock_sleep: MagicMock):
        attempts = 0

        def exp_backoff(prev: AttemptState | None, next: AttemptState) -> int:
            return 2 ** (next.attempt - 1)

        for attempt in attempting(until=AttemptsExhausted(4), wait=exp_backoff):
            with attempt:
                attempts += 1

                if attempts < 4:
                    raise Exception("fail")

        assert attempts == 4


class TestAsyncWait:
    @pytest.fixture
    def mock_sleep(self, monkeypatch: pytest.MonkeyPatch):
        mock_sleep = AsyncMock()
        monkeypatch.setattr("asyncio.sleep", mock_sleep)
        return mock_sleep

    @pytest.mark.parametrize("wait", [5, datetime.timedelta(minutes=5), 5.0])
    async def test_wait(
        self, wait: int | float | datetime.timedelta, mock_sleep: AsyncMock
    ):
        attempts = 0
        async for attempt in attempting_async(until=AttemptsExhausted(3), wait=wait):
            async with attempt:
                attempts += 1
                if attempts < 2:
                    raise Exception("Test exception")

        if isinstance(wait, datetime.timedelta):
            mock_sleep.assert_awaited_once_with(wait.total_seconds())
        else:
            mock_sleep.assert_awaited_once_with(wait)

    async def test_wait_with_exponential_backoff_callable(self, mock_sleep: AsyncMock):
        attempts = 0

        def exp_backoff(prev: AttemptState | None, next: AttemptState) -> int:
            return 2 ** (next.attempt - 1)

        async for attempt in attempting_async(
            until=AttemptsExhausted(4), wait=exp_backoff
        ):
            async with attempt:
                attempts += 1

                if attempts < 4:
                    raise Exception("fail")

        assert attempts == 4
