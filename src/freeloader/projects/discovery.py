from pathlib import Path


class ProjectDiscovery:
    MANIFEST_NAME = "freeloader.yaml"

    def find_manifest(self, start_dir: Path | None = None) -> Path | None:
        current = (start_dir or Path.cwd()).resolve()
        while True:
            candidate = current / self.MANIFEST_NAME
            if candidate.exists():
                return candidate
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    def find_project_root(self, start_dir: Path | None = None) -> Path | None:
        manifest = self.find_manifest(start_dir)
        if manifest:
            return manifest.parent
        return None
