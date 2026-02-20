# block

Block contract schema, DAG resolution, execution context, and blocks-root validation.

## Responsibilities

- Defines the `BlockContract` schema (provides, requires, config) parsed from `block.yml`
- Resolves a list of `BlockRef` objects into a topologically sorted `ResolvedBlock` list via `DAGResolver`
- Executes resolved blocks in order, injecting secrets and wiring outputs as inputs via `BlockRunner`
- Validates a blocks-root directory for structural correctness

## Public interface

```python
from freeloader.shared.block import (
    BlockRunner,
    BlocksRootInvalid,
    validate_blocks_root,
    DAGError,
    MissingRequirement,
    AmbiguousProvider,
    CircularDependency,
    DuplicateBlockId,
)

validate_blocks_root(blocks_root)

runner = BlockRunner(
    work_dir=work_dir,
    blocks_root=blocks_root,
    secrets_reader=read_secrets,
    terraform_factory=Terraform,
)
runner.run_all(resolved_blocks, context)
```
