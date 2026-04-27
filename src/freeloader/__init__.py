from importlib.metadata import PackageNotFoundError, version

from .shared.runtime import Freeloader

fl = Freeloader.from_env()

try:
    __version__ = version("freeloader")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = ["__version__", "fl"]
