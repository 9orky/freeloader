from __future__ import annotations

from freeloader.shared.console.progress import ProgressUpdate, run_status_stream


def test_run_status_stream_consumes_events_lazily_and_in_order(monkeypatch) -> None:
    import freeloader.shared.console.progress as progress

    lifecycle: list[tuple] = []
    observed: list[tuple[str, int]] = []

    class FakeStatusStream:
        def __init__(self, initial_status: str = "Working...") -> None:
            lifecycle.append(("init", initial_status))

        def __enter__(self) -> "FakeStatusStream":
            lifecycle.append(("enter",))
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            lifecycle.append(("exit", exc_type))

        def update(self, message: str) -> None:
            lifecycle.append(("update", message))

        def write_line(self, message: str, *, style: str | None = None) -> None:
            lifecycle.append(("line", message, style))

    def events():
        for item in (1, 2):
            observed.append(("yield", item))
            yield item

    def on_event(item: int) -> ProgressUpdate:
        observed.append(("map", item))
        return ProgressUpdate(status=f"status-{item}", line=f"line-{item}")

    monkeypatch.setattr(progress, "StatusStream", FakeStatusStream)

    run_status_stream(events(), initial_status="Starting...",
                      on_event=on_event)

    assert observed == [
        ("yield", 1),
        ("map", 1),
        ("yield", 2),
        ("map", 2),
    ]
    assert lifecycle == [
        ("init", "Starting..."),
        ("enter",),
        ("line", "line-1", None),
        ("update", "status-1"),
        ("line", "line-2", None),
        ("update", "status-2"),
        ("exit", None),
    ]
