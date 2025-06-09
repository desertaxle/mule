from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AttemptState:
    attempt: int
    exception: BaseException | None = None
    result: Any = ...
