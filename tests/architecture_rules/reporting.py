from .results import PipelineResult


def render_pipeline_result(result: PipelineResult) -> str:
    lines: list[str] = []
    for rule_result in result.results:
        lines.append(f"[{rule_result.title}] {rule_result.description}")
        if rule_result.passed:
            lines.append("  ✓ ok")
            continue
        for violation in rule_result.violations:
            lines.append(f"  ✗ {violation.message}")
    return "\n".join(lines)
