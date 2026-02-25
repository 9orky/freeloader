# block

Block contract schema, DAG resolution, execution context, and blocks-root validation.

## Responsibilities

- Defines the `BlockContract` schema (provides, requires, config) parsed from `block.yml`
- Resolves a list of `BlockRef` objects into a topologically sorted `ResolvedBlock` list via `DAGResolver`
- Executes resolved blocks in order, injecting secrets and wiring outputs as inputs via `BlockRunner`
- Validates a blocks-root directory for structural correctness

