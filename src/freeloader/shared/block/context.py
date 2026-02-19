from typing import Any


class ExecutionContext:
    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, Any]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, Any]) -> None:
        self._outputs[block_id] = outputs

    def get_output(self, block_id: str, key: str) -> Any:
        return self._outputs[block_id][key]

    def get_all_outputs(self, block_id: str) -> dict[str, Any]:
        return self._outputs.get(block_id, {})

    def has_outputs(self, block_id: str) -> bool:
        return block_id in self._outputs

    def all_outputs_flat(self) -> dict[str, Any]:
        flat: dict[str, Any] = {}
        for block_id, outputs in self._outputs.items():
            for key, value in outputs.items():
                flat[f"{block_id}.{key}"] = value
        return flat

    def resolve_inputs(self, inputs_map: dict[str, str]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for requires_key, provider_id in inputs_map.items():
            resolved[requires_key] = self.get_output(provider_id, requires_key)
        return resolved
