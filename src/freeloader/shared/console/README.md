# console

Terminal output formatting, raw input helpers, and CLI error handling decorators.

## Responsibilities

- Provides styled terminal output helpers: `info`, `success`, `warn`, `error`, `print_table`
- Provides `prompt` and `InputSelector` for terminal-safe input collection
- Provides `handle_cli_error` decorator for Click commands
- Provides `handle_errors` decorator for Typer commands

## Public interface

```python
from freeloader.shared.console import info, ok, warn, error, print_table
from freeloader.shared.console import InputSelector, handle_cli_error, handle_errors, prompt

info("Scanning hosts...")
ok("host-01 -> 10.0.0.1 (imported)")
warn("Orphan keys found: id_rsa")
error("Host 'prod' not found")
print_table("Inventory", ["Alias", "Host"], [["prod", "10.0.0.1"]])
prompt("Service provider token", hide_input=True)
InputSelector("Block input").ask()

@handle_cli_error   # Click commands
def my_command(): ...

@handle_errors      # Typer commands
def my_typer_command(): ...
```
