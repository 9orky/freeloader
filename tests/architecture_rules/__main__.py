from pathlib import Path

from . import ArchitectureContext, build_default_pipeline, render_pipeline_result


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    context = ArchitectureContext.for_repo_root(repo_root)
    result = build_default_pipeline().run(context)
    print(render_pipeline_result(result))
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
