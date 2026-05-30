"""Legacy synchronous database-session hook for tests and integrations."""

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def get_db() -> Iterator[None]:
    yield None
