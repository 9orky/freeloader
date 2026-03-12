from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import TracebackType
from typing import TypeVar

from . import _console


T = TypeVar("T")


@dataclass(frozen=True)
class ProgressUpdate:
    status: str | None = None
    line: str | None = None
    style: str | None = None


class StatusStream:
    def __init__(self, initial_status: str = "Working...") -> None:
        self._current_status = initial_status
        self._status = None

    def __enter__(self) -> "StatusStream":
        self._start_status(self._current_status)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._status is not None:
            self._status.__exit__(exc_type, exc, tb)
            self._status = None

    def update(self, message: str) -> None:
        assert self._status is not None
        self._current_status = message
        self._status.update(message)

    def write_line(self, message: str, *, style: str | None = None) -> None:
        assert self._status is not None
        self._status.__exit__(None, None, None)
        self._status = None
        _console.print(message, style=style)
        self._start_status(self._current_status)

    def _start_status(self, message: str) -> None:
        self._status = _console.status(message)
        self._status.__enter__()


def run_status_stream(
    events: Iterable[T],
    *,
    initial_status: str,
    on_event: Callable[[T], ProgressUpdate | None],
) -> None:
    with StatusStream(initial_status=initial_status) as stream:
        for event in events:
            update = on_event(event)
            if update is None:
                continue
            if update.line is not None:
                stream.write_line(update.line, style=update.style)
            if update.status is not None:
                stream.update(update.status)


__all__ = ["ProgressUpdate", "StatusStream", "run_status_stream"]
