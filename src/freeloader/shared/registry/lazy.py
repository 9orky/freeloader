import threading
from typing import TypeVar, Type, Dict, Generic, Callable

T = TypeVar("T")


class LazyRegistry(Generic[T]):
    def __init__(self, name: str = "GenericRegistry"):
        self.name = name
        self._classes: Dict[str, Type[T]] = {}
        self._instances: Dict[str, T] = {}
        self._lock = threading.Lock()

    def register(self, key: str) -> Callable[[Type[T]], Type[T]]:
        def decorator(cls: Type[T]) -> Type[T]:
            if key in self._classes:
                raise ValueError(f"Key '{key}' is already registered in {self.name}.")

            self._classes[key] = cls
            return cls
        return decorator
    
    def find_all(self) -> Dict[str, T]:
        return {key: self.get(key) for key in self._classes.keys()}

    def get(self, key: str) -> T:
        if key not in self._instances:
            with self._lock:
                if key not in self._instances:
                    if key not in self._classes:
                        raise KeyError(f"'{key}' not found in {self.name}")

                    print(f"[*] Initializing {key}...")
                    cls = self._classes[key]
                    self._instances[key] = cls()

        return self._instances[key]

