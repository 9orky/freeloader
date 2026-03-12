import dataclasses
from pathlib import Path

from freeloader.shared.tech import TechFacade

from ..domain.entities import TechStack
from ..domain.repository import TechStackDetector


class TechFacadeDetector(TechStackDetector):
    def detect(self, folder: Path) -> TechStack | None:
        detected = TechFacade().detect_stack(folder)
        if not detected:
            return None
        known_fields = {f.name for f in dataclasses.fields(TechStack)}
        filtered = {k: v for k, v in detected.items() if k in known_fields}
        return TechStack(**filtered)
