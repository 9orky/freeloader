import subprocess
import sys
from pathlib import Path

from freeloader.shared.errors import SubprocessDetail, SubprocessError

STREAM_OUTPUT: bool = False


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
        if STREAM_OUTPUT:
            return _run_streaming(args, cwd=cwd, env=env, timeout=timeout)
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


def _run_streaming(
    args: list[str],
    *,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.Popen(
        args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    lines: list[str] = []
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stderr.write(line)
            lines.append(line)
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise
    output = "".join(lines)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode, args, output=output, stderr=""
        )
    return subprocess.CompletedProcess(args, proc.returncode, stdout=output, stderr="")
