# runtime

Freeloader home directory layout, feature path derivations, and the eventsourcing application base.

## Responsibilities

- Manages the Freeloader home folder (`~/.freeloader` or `$FREELOADER_HOME`) and its sub-directories
- Exposes the `FreeloaderApplication` base class pre-configured with the SQLite event store
- Derives well-known feature paths (e.g. `hosts_path`) from the home directory

## Public interface

```python
from freeloader.shared.runtime import Freeloader, FreeloaderApplication, hosts_path

fl = Freeloader()
fl.must_be_installed()
project_dir = fl.build_managed_project_path("my-app")

class MyApp(FreeloaderApplication): ...

path = hosts_path()  # ~/.freeloader/hosts
```
