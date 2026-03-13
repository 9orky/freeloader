from __future__ import annotations

from pathlib import Path

from freeloader.block.infrastructure.loader import FileSystemBlockLoader
from freeloader.shared.tech import TECH_STACK_FIELD_NAMES

BLOCKS_ROOT = Path(__file__).parent.parent / "src" / "blocks"


def test_blocks_load() -> None:
    loader = FileSystemBlockLoader.init(BLOCKS_ROOT)
    blocks = loader.load_all()
    assert blocks, "No blocks found"

    for block_id, block in blocks.items():
        contract = block.contract
        assert contract.block.layer, f"Block {block_id} has no layer"
        assert contract.config is not None, f"Block {block_id} has no config"

        for field in contract.config:
            assert field.group in ("basic", "advanced", "secrets"), (
                f"Block {block_id} field {field.name} has invalid group {field.group}"
            )


def test_tech_stack_blocks_have_tech_fields() -> None:
    loader = FileSystemBlockLoader.init(BLOCKS_ROOT)
    for block_id, block in loader.load_all().items():
        contract = block.contract
        if contract.block.required_tech_stack:
            tech_stack_fields = [
                field.name for field in contract.config if field.name in TECH_STACK_FIELD_NAMES
            ]
            assert tech_stack_fields, (
                f"Block {block_id} is marked required_tech_stack but has no tech stack fields"
            )


def test_gcp_blocks_expose_expected_contracts() -> None:
    loader = FileSystemBlockLoader.init(BLOCKS_ROOT)
    blocks = loader.load_all()

    artifact_registry = blocks["gcp.artifact_registry"].contract
    assert artifact_registry.block.layer == "registry"
    assert {"host", "user", "token", "image_path"}.issubset(
        artifact_registry.provides)
    assert any(
        field.name == "gcp_service_account_json" for field in artifact_registry.config)

    cloud_run = blocks["gcp.cloud_run"].contract
    assert cloud_run.block.layer == "deploy"
    assert "registry.image_path" in cloud_run.requires
    assert {"app_url", "app_id"}.issubset(cloud_run.provides)

    vm = blocks["gcp.vm"].contract
    assert vm.block.layer == "infra"
    assert {"ip_address", "instance_id", "ssh_user",
            "public_dns"}.issubset(vm.provides)
    assert "ssh_private_key_path" in vm.provides
    assert any(field.name == "ssh_public_key" for field in vm.config)
