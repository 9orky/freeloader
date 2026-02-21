from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod

from .contract import BlockContract


@dataclass(frozen=True)
class Block:
    folder: Path
    contract_file: Path
    terraform_file: Path

    @property
    def id(self) -> str:
        block_name = self.folder.name
        provider_name = self.folder.parent.name
        return f"{provider_name}.{block_name}"
    
    @property
    def contract(self) -> BlockContract:
        from freeloader import io
        return io.load_yaml_model(self.contract_file, BlockContract)
    
    @property
    def requires_auth(self) -> bool:
        return self.contract.config_fields("secrets") != []
    
    def dump_config(self, full: bool = False) -> dict[str, str]:
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


class BlockProvider:
    def __init__(self, folder: Path) -> None:
        self._folder = folder

    @property
    def blocks(self) -> list[Block]:
        return [Block.from_folder(f) for f in self._folder.glob("*") if f.is_dir()]

    def get_block(self, name: str) -> Block:
        block = [b for b in self.blocks if b.folder.name == name]
        if not block:
            raise ValueError(f"Block '{name}' not found")

        return block[0]
    

@dataclass(frozen=True)
class BlockRepository:
    folder: Path

    @classmethod
    def load(cls, path: Path) -> "BlockRepository":
        assert path.is_dir(), f"Blocks root {path} is not a directory"
        return cls(folder=path)
    
    @property
    def providers(self) -> list[BlockProvider]:
        return [BlockProvider(p) for p in self.folder.glob("*") if p.is_dir()]
    
    def get_by_names(self, names: list[str]) -> list[BlockProvider]:
        return [p for p in self.providers if p._folder.name in names]


class TerraformBridge(ABC):
    @abstractmethod
    def create(self) -> None: ...

    @abstractmethod
    def destroy(self) -> None: ...


class SecretsBridge(ABC):
    @abstractmethod
    def read(self, secret_names: list[str]) -> dict[str, str]: ...
