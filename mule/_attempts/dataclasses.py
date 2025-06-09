from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AttemptState:
    """
    A dataclass that represents the state of an attempt.

    Args:
        attempt: The attempt number.
        exception: The exception that occurred, if any.
        result: The result of the attempt, if any. Ellipsis is used as a sentinel
            to indicate that a result has not been set yet.
    """

    attempt: int
    exception: BaseException | None = None
    result: Any = ...
