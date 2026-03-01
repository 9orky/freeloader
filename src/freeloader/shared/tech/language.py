from pathlib import Path
import re
from typing import Protocol
import subprocess


class LanguageSource(Protocol):
    def detect(self, project_dir: Path) -> str | None: ...


class FileBasedLanguageSource(LanguageSource):
    file_patterns: list[str]

    def detect(self, project_dir: Path) -> str | None:
        for pattern in self.file_patterns:
            if any(project_dir.glob(pattern)):
                return self._extract_version(project_dir / pattern)
        return None

    def _extract_version(self, language_version_file: Path) -> str | None:
        if language_version_file.exists():
            return language_version_file.read_text().strip()
        return None
    

class LocalhostCommandLineSource(LanguageSource):
    commands: list[str]
    version_pattern: str

    def detect(self, project_dir: Path) -> str | None:
        for command in self.commands:
            try:
                result = subprocess.run(command, cwd=project_dir, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    output = result.stdout.strip() or result.stderr.strip()
                    match = re.search(self.version_pattern, output)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        return None