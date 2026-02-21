from pathlib import Path

import dotenv
dotenv.load_dotenv()

from .shared import console, cli, io, tech, block, registry
from .shared.runtime import Freeloader


runtime = Freeloader.from_env(Path.cwd())


__all__ = [
    "console",
    "cli",
    "io",
    "tech",
    "block",
    "registry",
    "runtime",
]