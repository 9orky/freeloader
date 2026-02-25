from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod

from .contract import BlockContract


class BlockError(Exception):
    pass


class BlockId(str):
    def __new__(cls, value: str):
        if "." not in value:
            raise ValueError(f"Invalid block id '{value}', expected format 'provider.block'")
        return str.__new__(cls, value)
    

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

    def get_by_id(self, block_id: BlockId) -> Block | None:
        provider_name, block_name = block_id.split(".")
        
        provider = next((p for p in self.providers if p._folder.name == provider_name), None)
        if not provider:
            raise BlockError(f"Provider '{provider_name}' not found for block '{block_id}'")
        
        block = next((b for b in provider.blocks if b.folder.name == block_name), None)
        if not block:
            raise BlockError(f"Block '{block_name}' not found for block '{block_id}'")
        
        return block


class TerraformBridge(ABC):
    @abstractmethod
    def create(self) -> None: ...

    @abstractmethod
    def destroy(self) -> None: ...


class SecretsBridge(ABC):
    @abstractmethod
    def read(self, secret_names: list[str]) -> dict[str, str]: ...
