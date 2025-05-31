from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from typing_extensions import Protocol

if TYPE_CHECKING:
    from .dataclasses import AttemptState  # pragma: no cover


class WaitTimeProvider(Protocol):
    """
    Protocol for callables that produce a wait time given the previous and next AttemptState.

    Args:
        prev: The previous AttemptState, or None if this is the first attempt.
        next: The next AttemptState (the one about to be run).

    Returns:
        The wait time as a timedelta, seconds (int/float), or None.
    """

    def __call__(
        self, prev: "AttemptState | None", next: "AttemptState"
    ) -> datetime.timedelta | int | float | None: ...
