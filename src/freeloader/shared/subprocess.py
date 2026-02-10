import subprocess
from pathlib import Path

from freeloader.shared.errors import SubprocessDetail, SubprocessError


def run(
    args: list[str],
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    label: str = "",
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    cwd_str = str(cwd) if cwd else "."
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise SubprocessError(
            label or f"Command timed out: {args[0]}",
            SubprocessDetail(
                command=args,
                exit_code=-1,
                stderr=f"Process timed out after {timeout}s",
                stdout="",
                cwd=cwd_str,
            ),
        ) from None
    except subprocess.CalledProcessError as exc:
        raise SubprocessError(
            label or f"Command failed: {args[0]}",
            SubprocessDetail(
                command=args,
                exit_code=exc.returncode,
                stderr=exc.stderr or "",
                stdout=exc.stdout or "",
                cwd=cwd_str,
            ),
        ) from None
    except FileNotFoundError:
        raise SubprocessError(
            f"Binary not found: {args[0]}",
            SubprocessDetail(
                command=args,
                exit_code=-1,
                stderr=f"'{args[0]}' is not installed or not in PATH",
                stdout="",
                cwd=cwd_str,
            ),
        ) from None
