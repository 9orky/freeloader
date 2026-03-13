from pathlib import Path

import pytest

from tests.architecture_rules import (
    ArchitectureContext,
    build_default_pipeline,
    render_pipeline_result,
)


def test_architecture() -> None:
    context = ArchitectureContext.for_repo_root(
        Path(__file__).resolve().parents[1])
    result = build_default_pipeline().run(context)
    print()
    print(render_pipeline_result(result))
    if result.failed:
        pytest.fail("Architecture violations detected (see above)",
                    pytrace=False)


if __name__ == "__main__":
    context = ArchitectureContext.for_repo_root(
        Path(__file__).resolve().parents[1])
    result = build_default_pipeline().run(context)
    print()
    print(render_pipeline_result(result))
    raise SystemExit(1 if result.failed else 0)
