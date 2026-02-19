from eventsourcing.application import Application

from .fl import Freeloader


class FreeloaderApplication(Application):
    env = {
        "INFRASTRUCTURE_FACTORY": "eventsourcing.sqlite:Factory",
        "SQLITE_DBNAME": str(Freeloader().home / "freeloader.db"),
    }
