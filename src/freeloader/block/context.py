from dataclasses import dataclass

from freeloader.shared.types import ConfigValue


@dataclass(frozen=True)
class OutputReference:
    requirement_key: str
    provider_id: str
    output_name: str

    @classmethod
    def from_input(cls, requirement_key: str, provider_id: str) -> "OutputReference":
        _, output_name = requirement_key.split(".", 1)
        return cls(
            requirement_key=requirement_key,
            provider_id=provider_id,
            output_name=output_name,
        )

    @property
    def tfvar_name(self) -> str:
        return self.requirement_key.replace(".", "_")


@dataclass(frozen=True)
class ResolvedInput:
    reference: OutputReference
    value: ConfigValue | None

    @property
    def tfvar_name(self) -> str:
        return self.reference.tfvar_name


class ExecutionContext:
    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, ConfigValue | None]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, ConfigValue | None]) -> None:
        self._outputs[block_id] = outputs

    def get_output(self, block_id: str, key: str) -> ConfigValue | None:
        return self._outputs[block_id][key]

    def get_all_outputs(self, block_id: str) -> dict[str, ConfigValue | None]:
        return dict(self._outputs.get(block_id, {}))

    def has_outputs(self, block_id: str) -> bool:
        return block_id in self._outputs

    def resolve_inputs(self, inputs_map: dict[str, str]) -> list[ResolvedInput]:
        result: list[ResolvedInput] = []
        for req_key, provider_id in inputs_map.items():
            reference = OutputReference.from_input(req_key, provider_id)
            result.append(
                ResolvedInput(
                    reference=reference,
                    value=self.get_output(
                        reference.provider_id, reference.output_name),
                )
            )
        return result
