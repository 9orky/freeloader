from pathlib import Path

import dotenv
dotenv.load_dotenv()

from .shared import console, cli, io, logger, tech, registry
from .shared.runtime import Freeloader


runtime = Freeloader.from_env(Path.cwd())


__all__ = [
    "console",
    "cli",
    "io",
    "logger",
    "tech",
    "registry",
    "runtime",
]