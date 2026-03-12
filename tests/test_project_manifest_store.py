from pathlib import Path

from freeloader.project.infrastructure.manifest_store import YamlManifestStore
from freeloader.shared.tech import TechStack


def test_manifest_store_round_trips_framework(tmp_path: Path) -> None:
    store = YamlManifestStore()

    store.save(
        name="demo",
        folder=tmp_path,
        tech_stack=TechStack(
            language="python",
            language_version="3.12",
            package_manager="uv",
            framework="fastapi",
        ),
        block_configs={"github.actions_ci": {"name": "demo"}},
    )

    manifest = store.load(tmp_path)

    assert manifest.tech_stack.framework == "fastapi"
    assert manifest.tech_stack.language == "python"
