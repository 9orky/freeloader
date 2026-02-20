# console

Terminal output formatting and CLI error handling decorators.

## Responsibilities

- Provides styled terminal output helpers: `info`, `success`, `warn`, `error`, `print_table`
- Provides `handle_cli_error` decorator for Click commands
- Provides `handle_errors` decorator for Typer commands

## Public interface

```python
from freeloader.shared.console import info, success, warn, error, print_table
from freeloader.shared.console import handle_cli_error, handle_errors

info("Scanning hosts...")
success("host-01 → 10.0.0.1 (imported)")
warn("Orphan keys found: id_rsa")
error("Host 'prod' not found")
print_table("Inventory", ["Alias", "Host"], [["prod", "10.0.0.1"]])

@handle_cli_error   # Click commands
def my_command(): ...

@handle_errors      # Typer commands
def my_typer_command(): ...
```
