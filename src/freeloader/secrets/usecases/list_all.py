from ._storage import load_storage


def list_all(namespace: str | None = None):
    storage = load_storage()
    pass