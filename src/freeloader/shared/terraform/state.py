from enum import Enum

class ResourceState(Enum):
    INITIATED = "initiated"
    PLANNED = "planned"
    APPLIED = "applied"
    DESTROYED = "destroyed"
    UNKNOWN = "unknown"
