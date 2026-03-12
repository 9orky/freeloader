from dataclasses import dataclass
from pathlib import Path

from freeloader.shared import io
from ..domain.entity import Block, BlockContract
from ..domain.repository import BlockRepository
from ..domain.value_object import BlockId

from .block import SourceBlock


@dataclass(frozen=True)
class FileSystemBlockLoader(BlockRepository):
    folder: Path

    @classmethod
    def init(cls, path: Path) -> "FileSystemBlockLoader":
        assert path.is_dir(), f"Blocks root {path} is not a directory"
        return cls(folder=path)

    # ── BlockRepository ABC ──────────────────────────────────────────────────

    def load_all(self) -> dict[str, Block]:
        return {bid: sb.block for bid, sb in self._scan().items()}

    def load_by_ids(self, block_ids: list[BlockId]) -> dict[str, Block]:
        return {str(bid): self._load_source(bid).block for bid in block_ids}

    def dump_assets(self, block_id: BlockId, target: Path) -> None:
        self._load_source(block_id).dump_assets(target)

    # ── Convenience helper ───────────────────────────────────────────────────

    def load_by_refs(self, block_refs: list) -> dict[str, Block]:
        block_ids = [BlockId(ref.resolved_id) for ref in block_refs]
        return self.load_by_ids(block_ids)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _scan(self) -> dict[str, SourceBlock]:
        result: dict[str, SourceBlock] = {}
        for provider_folder in self.folder.iterdir():
            if not provider_folder.is_dir():
                continue
            for block_folder in provider_folder.iterdir():
                if not block_folder.is_dir():
                    continue
                sb = self._source_block_from_folder(block_folder)
                result[str(sb.block.id)] = sb
        return result

    def _load_source(self, block_id: BlockId) -> SourceBlock:
        block_folder = self.folder / block_id.sub_path
        return self._source_block_from_folder(block_folder)

    @staticmethod
    def _source_block_from_folder(folder: Path) -> SourceBlock:
        contract_file = folder / "block.yml"
        assert contract_file.exists(), f"Contract file not found in {folder}"
        assert (
            folder / "main.tf").exists(), f"Terraform file not found in {folder}"

        block_name = folder.name
        provider_name = folder.parent.name
        block_id = BlockId(f"{provider_name}.{block_name}")

        # Normalise grouped YAML config format before Pydantic validation.
        # The YAML may use {basic: [...], advanced: [...], secrets: [...]} for
        # readability; the domain model only understands the canonical flat list.
        raw = io.load_yaml(contract_file)
        if isinstance(raw.get("config"), dict):
            flat: list[dict] = []
            for group_name in ("basic", "advanced", "secrets"):
                for entry in raw["config"].get(group_name) or []:
                    entry["group"] = group_name
                    flat.append(entry)
            raw["config"] = flat
        contract = BlockContract.model_validate(raw)

        return SourceBlock(
            block=Block(id=block_id, contract=contract),
            source_folder=folder,
        )
