from __future__ import annotations

import ast

from ..context import ArchitectureContext
from .base import ArchitectureRule


class DeepRelativeImportRule(ArchitectureRule):
    rule_id = "deep_relative_imports"
    title = "Deep Relative Imports"
    description = "Feature modules may not use relative imports above the parent folder"

    def violations(self, context: ArchitectureContext):
        result = []
        for feature_dir in context.feature_packages():
            for py_file in sorted(feature_dir.rglob("*.py")):
                tree = context.parse_file(py_file)
                if tree is None:
                    continue

                module = context.file_to_module(py_file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.level > 2:
                        result.append(
                            self.violation(
                                f"{module}:{node.lineno} uses {'.' * node.level}{node.module or ''}"
                            )
                        )
        return result
