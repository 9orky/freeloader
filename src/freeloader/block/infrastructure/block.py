from dataclasses import dataclass
from pathlib import Path

from ..base import BlockId
from ..contract import BlockContract


@dataclass(frozen=True)
class Block:
    folder: Path
    contract_file: Path
    terraform_file: Path

    @property
    def id(self) -> BlockId:
        block_name = self.folder.name
        provider_name = self.folder.parent.name
        return BlockId(f"{provider_name}.{block_name}")

    @property
    def contract(self) -> BlockContract:
        from freeloader import io
        return io.load_yaml_model(self.contract_file, BlockContract)

    @property
    def requires_auth(self) -> bool:
        return self.contract.config_fields("secrets") != []

    def dump_config(self, full: bool) -> dict[str, str]:
        groups = ["basic"]
        if full:
            groups.append("advanced")

        return self.contract.collect_defaults(groups)

    @classmethod
    def from_folder(cls, folder: Path) -> "Block":
        contract_file = folder / "block.yml"
        terraform_file = folder / "main.tf"

        assert contract_file.exists(), f"Contract file not found in {folder}"
        assert terraform_file.exists(), f"Terraform file not found in {folder}"

        return cls(
            folder=folder,
            contract_file=contract_file,
            terraform_file=terraform_file,
        )
