from __future__ import annotations

from pathlib import Path

import hcl2
from pydantic import ValidationError

import yaml

from .config import BlockContract


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


class BlocksRootInvalid(Exception):
    pass


class _BlockChecker:
    _next: _BlockChecker | None = None

    def set_next(self, checker: _BlockChecker) -> _BlockChecker:
        self._next = checker
        return checker

    def check(self, blocks_root: Path) -> list[str]:
        return []

    def _run_chain(self, blocks_root: Path) -> list[str]:
        violations = self.check(blocks_root)
        if self._next:
            violations += self._next._run_chain(blocks_root)
        return violations

    def _block_dirs(self, blocks_root: Path) -> list[Path]:
        return sorted(
            leaf
            for provider in blocks_root.iterdir()
            if provider.is_dir()
            for leaf in provider.iterdir()
            if leaf.is_dir()
        )


class _MainTFPresenceChecker(_BlockChecker):
    def check(self, blocks_root: Path) -> list[str]:
        return [
            f"{d.relative_to(blocks_root)}: missing main.tf"
            for d in self._block_dirs(blocks_root)
            if not (d / "main.tf").exists()
        ]


class _BlockYmlPresenceChecker(_BlockChecker):
    def check(self, blocks_root: Path) -> list[str]:
        return [
            f"{d.relative_to(blocks_root)}: missing block.yml"
            for d in self._block_dirs(blocks_root)
            if not (d / "block.yml").exists()
        ]


class _BlockYmlValidationChecker(_BlockChecker):
    def check(self, blocks_root: Path) -> list[str]:
        result: list[str] = []
        for d in self._block_dirs(blocks_root):
            yml = d / "block.yml"
            if not yml.exists():
                continue
            try:
                BlockContract.model_validate(_load_yaml(yml))
            except ValidationError as exc:
                result.append(f"{d.relative_to(blocks_root)}: {exc}")
        return result


class _TerraformSyntaxChecker(_BlockChecker):
    def check(self, blocks_root: Path) -> list[str]:
        result: list[str] = []
        for d in self._block_dirs(blocks_root):
            tf = d / "main.tf"
            if not tf.exists():
                continue
            try:
                with tf.open() as fh:
                    hcl2.load(fh)
            except Exception as exc:
                result.append(f"{d.relative_to(blocks_root)}: {exc}")
        return result


def validate_blocks_root(blocks_root: Path) -> None:
    head = _MainTFPresenceChecker()
    head.set_next(_BlockYmlPresenceChecker()).set_next(
        _BlockYmlValidationChecker()).set_next(_TerraformSyntaxChecker())
    violations = head._run_chain(blocks_root)
    if violations:
        raise BlocksRootInvalid("\n".join(violations))
