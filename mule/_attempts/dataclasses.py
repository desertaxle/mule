from dataclasses import dataclass


@dataclass
class AttemptState:
    attempt: int
    exception: BaseException | None = None
