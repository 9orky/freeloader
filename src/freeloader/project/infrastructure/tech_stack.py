from pathlib import Path

from freeloader.shared.tech import TechFacade

from ..domain.entity import TechStack
from ..domain.repository import TechStackDetector


class TechFacadeDetector(TechStackDetector):
    def detect(self, folder: Path) -> TechStack | None:
        return TechFacade().detect_stack(folder)
