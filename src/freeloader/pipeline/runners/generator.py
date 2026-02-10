import os
from pathlib import Path
from typing import Any

import jinja2

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.shared.errors import FeasibilityIssue


class GeneratorRunner(BaseRunner):
    def __init__(self, output_dir: Path, block_dirs: dict[str, Path]) -> None:
        self._output_dir = output_dir
        self._block_dirs = block_dirs

    def runner_name(self) -> str:
        return "generator"

    def check_feasibility(self, blocks: list[ResolvedBlock]) -> list[FeasibilityIssue]:
        issues: list[FeasibilityIssue] = []
        name = self.runner_name()

        if not self._output_dir.exists():
            issues.append(FeasibilityIssue(
                runner=name, check="output directory",
                detail=f"Output directory does not exist: {self._output_dir}",
            ))
        elif not os.access(self._output_dir, os.W_OK):
            issues.append(FeasibilityIssue(
                runner=name, check="output directory writable",
                detail=f"Cannot write to output directory: {self._output_dir}",
            ))

        for block in blocks:
            block_name = block.contract.block.name
            block_dir = self._block_dirs.get(block_name)
            if not block_dir:
                issues.append(FeasibilityIssue(
                    runner=name, check=f"block dir for '{block_name}'",
                    detail=f"No block directory registered for '{block_name}'",
                ))
                continue
            templates_dir = block_dir / "templates"
            if not templates_dir.exists():
                issues.append(FeasibilityIssue(
                    runner=name, check=f"templates for '{block_name}'",
                    detail=f"Templates directory missing: {templates_dir}",
                ))

        return issues

    def plan(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> str:
        lines: list[str] = []
        for block in blocks:
            templates_dir = self._get_templates_dir(block)
            if not templates_dir:
                continue
            for tpl_path in self._select_templates(block, templates_dir):
                target = self._target_path(tpl_path)
                status = "overwrite" if target.exists() else "create"
                lines.append(
                    f"  [{status}] {target.relative_to(self._output_dir)}")
        return "\n".join(lines) if lines else "  (no files to generate)"

    def apply(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> dict[str, dict[str, Any]]:
        all_outputs: dict[str, dict[str, Any]] = {}
        for block in blocks:
            templates_dir = self._get_templates_dir(block)
            if not templates_dir:
                all_outputs[block.ref.resolved_id] = {}
                continue

            template_context = self._build_context(block, ctx)
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(templates_dir)),
                keep_trailing_newline=True,
                undefined=jinja2.StrictUndefined,
            )

            generated: list[str] = []
            for tpl_path in self._select_templates(block, templates_dir):
                template = env.get_template(tpl_path.name)
                rendered = template.render(**template_context)
                target = self._target_path(tpl_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(rendered)
                generated.append(str(target.relative_to(self._output_dir)))

            all_outputs[block.ref.resolved_id] = {"generated_files": generated}
        return all_outputs

    def destroy(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> None:
        for block in blocks:
            templates_dir = self._get_templates_dir(block)
            if not templates_dir:
                continue
            for tpl_path in self._select_templates(block, templates_dir):
                target = self._target_path(tpl_path)
                if target.exists():
                    target.unlink()

    def _select_templates(
        self, block: ResolvedBlock, templates_dir: Path,
    ) -> list[Path]:
        block_name = block.contract.block.name
        all_j2 = sorted(templates_dir.glob("*.j2"))

        if block_name != "dockerfile":
            return all_j2

        chosen = self._resolve_dockerfile_template(block)
        selected: list[Path] = []
        for p in all_j2:
            if p.name.endswith(".Dockerfile.j2"):
                prefix = p.name.removesuffix(".Dockerfile.j2")
                if prefix == chosen:
                    selected.append(p)
            else:
                selected.append(p)
        return selected

    def _resolve_dockerfile_template(self, block: ResolvedBlock) -> str:
        config = block.ref.config
        tpl = config.get("template", "auto")
        serve = config.get("serve_with", "nginx")

        if tpl != "auto":
            return tpl

        pm = self._detect_package_manager()
        return f"node-{pm}-{serve}"

    def _detect_package_manager(self) -> str:
        if (self._output_dir / "pnpm-lock.yaml").exists():
            return "pnpm"
        return "npm"

    def _get_templates_dir(self, block: ResolvedBlock) -> Path | None:
        block_name = block.contract.block.name
        block_dir = self._block_dirs.get(block_name)
        if block_dir:
            candidate = block_dir / "templates"
            if candidate.exists():
                return candidate
        return None

    def _target_path(self, template_path: Path) -> Path:
        name = template_path.name.removesuffix(".j2")
        if name.endswith(".Dockerfile"):
            return self._output_dir / "Dockerfile"
        if name == "dockerignore":
            return self._output_dir / ".dockerignore"
        if name.endswith(".yml") or name.endswith(".yaml"):
            return self._output_dir / ".github" / "workflows" / name
        return self._output_dir / name

    def _build_context(self, block: ResolvedBlock, ctx: ExecutionContext) -> dict[str, Any]:
        context: dict[str, Any] = {"config": block.ref.config}
        for req_key, provider_id in block.inputs.items():
            namespace, _, key = req_key.partition(".")
            if namespace not in context:
                context[namespace] = {}
            outputs = ctx.get_all_outputs(provider_id)
            context[namespace][key] = outputs.get(req_key, "")
        for provider_id in set(block.inputs.values()):
            outputs = ctx.get_all_outputs(provider_id)
            for out_key, out_val in outputs.items():
                ns, _, k = out_key.partition(".")
                if ns not in context:
                    context[ns] = {}
                context[ns][k] = out_val

        # Inject detected project metadata so templates can adapt
        context["detected"] = {
            "package_manager": self._detect_package_manager(),
        }
        return context
