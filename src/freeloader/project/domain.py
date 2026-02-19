from uuid import UUID

from eventsourcing.domain import Aggregate, event


class Project(Aggregate):
    class Registered(Aggregate.Created):
        path: str
        name: str

    class TechStackDetected(Aggregate.Event):
        language: str
        package_manager: str

    class Discarded(Aggregate.Event):
        def mutate(self, aggregate):
            super().mutate(aggregate)
            return None

    @event(Registered)
    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = path
        self.tech_stack = None

    @event(TechStackDetected)
    def detect_tech_stack(self, language: str, package_manager: str) -> None:
        self.tech_stack = {
            "language": language,
            "package_manager": package_manager
        }

    @event(Discarded)
    def discard(self) -> None:
        pass
