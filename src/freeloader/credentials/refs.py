import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from freeloader.pipeline.context import ExecutionContext
    from freeloader.credentials.vault import SecretVault

VAULT_PATTERN = re.compile(r"\{\{vault:(\w+)\}\}")
BLOCK_REF_PATTERN = re.compile(r"\{\{(\w[\w-]*)\.([\w.]+)\}\}")


def resolve_vault_refs(text: str, vault: "SecretVault") -> str:
    def _replace(m: re.Match[str]) -> str:
        return vault.get(m.group(1))

    return VAULT_PATTERN.sub(_replace, text)


def resolve_block_refs(text: str, context: "ExecutionContext") -> str:
    def _replace(m: re.Match[str]) -> str:
        block_id = m.group(1)
        key = m.group(2)
        return str(context.get_output(block_id, key))

    return BLOCK_REF_PATTERN.sub(_replace, text)


def resolve_all_refs(
    value: Any,
    vault: "SecretVault | None" = None,
    context: "ExecutionContext | None" = None,
) -> Any:
    if isinstance(value, str):
        if vault:
            value = resolve_vault_refs(value, vault)
        if context:
            value = resolve_block_refs(value, context)
        return value
    if isinstance(value, dict):
        return {k: resolve_all_refs(v, vault, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_all_refs(v, vault, context) for v in value]
    return value
