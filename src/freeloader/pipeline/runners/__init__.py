from freeloader.pipeline.blocks.models import RunnerType
from freeloader.pipeline.runners.base import BaseRunner


class RunnerRegistry:
    def __init__(self) -> None:
        self._runners: dict[RunnerType, BaseRunner] = {}

    def register(self, runner_type: RunnerType, runner: BaseRunner) -> None:
        self._runners[runner_type] = runner

    def get(self, runner_type: RunnerType) -> BaseRunner:
        return self._runners[runner_type]
