class BlockError(Exception):
    pass


class DAGError(Exception):
    ...


class MissingRequirement(DAGError):
    ...


class AmbiguousProvider(DAGError):
    ...


class CircularDependency(DAGError):
    ...


class DuplicateBlockId(DAGError):
    ...
