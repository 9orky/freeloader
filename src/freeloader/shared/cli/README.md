# cli

Subprocess execution and deterministic path-to-UUID identity.

## Responsibilities

- Runs external CLI commands and captures stdout as a structured `CommandOutput`
- Raises `CliCommandFailed` with stderr on non-zero exit
- Derives a stable, namespace-scoped UUID from an absolute filesystem path

## Public interface

```python
from freeloader.shared.cli import run_cli, path_to_id, CliCommandFailed, CommandOutput

output: CommandOutput = run_cli(["git", "status"], chdir=Path("/repo"))
print(output.raw)
print(output.json)

uid = path_to_id("/home/user/project")
```
