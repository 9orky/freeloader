from typing import Any


class ExecutionContext:
    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, Any]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, Any]) -> None:
        self._outputs[block_id] = outputs

    def get_output(self, block_id: str, key: str) -> Any:
        return self._outputs[block_id][key]

    def get_all_outputs(self, block_id: str) -> dict[str, Any]:
        return dict(self._outputs.get(block_id, {}))

    def has_outputs(self, block_id: str) -> bool:
        return block_id in self._outputs

    def resolve_inputs(self, inputs_map: dict[str, str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for req_key, provider_id in inputs_map.items():
            output_name = req_key.split(".", 1)[1]
            result[req_key] = self.get_output(provider_id, output_name)
        return result
