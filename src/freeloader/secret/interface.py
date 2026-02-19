"""
public interface for other modules to interact with secrets
"""
from . import use_cases


def read_secret(namespace: str, secret_name: str) -> str:
    pass


def write_secret(namespace: str, secret_name: str, secret_value: str) -> None:
    pass


def has_secret(namespace: str, secret_name: str) -> bool:
    pass