# Block System — Provision Orchestration Plan

## Scope

This plan covers the completion of two stubs:

| File | Current state | Target state |
|---|---|---|
| `provisioner.py` | `Provisioner.provision()` stops after DAG resolution | Full orchestration loop with progress tracking |
| `provision/progress.py` | `ProvisionProgress` references `provision.json` but has no logic | Complete state machine |
| `provision/state.py` | Does not exist | New module: serialisable state models |
| `provision/__init__.py` | Empty | Exports public surface |

---

## Module: `provision/state.py` (new)

Owned entirely by the `provision` package. Defines the serialisable state written to `provision.json`.

### Types

```
BlockStatus(str, Enum)
    pending   — not yet started
    running   — currently executing (set before runner is called; indicates crash if still set on next load)
    done      — completed successfully; outputs available
    failed    — execution raised an exception; error message stored

BlockRecord(BaseModel)
    status:  BlockStatus
    outputs: dict[str, Any]   — populated when status == done
    error:   str | None       — populated when status == failed

ProvisionState(BaseModel)
    blocks: dict[str, BlockRecord]   — keyed by resolved_id
```

### Behaviour notes

- `BlockRecord.outputs` and `BlockRecord.error` are mutually exclusive at runtime; both are stored as nullable fields to allow round-trip serialisation without a union discriminator.
- `BlockStatus.running` surviving a reload signals an interrupted run. The provisioner treats such entries as `pending` on resume (retry semantics).

---

## Module: `provision/progress.py` (complete)

```
ProvisionProgress
    __init__(root: Path, resolved_blocks: list[ResolvedBlock]) -> None
        _state_file: Path  = root / "provision.json"
        _state: ProvisionState = _load_state()

    _load_state() -> ProvisionState
        — Reads _state_file if it exists and parses with ProvisionState.model_validate_json.
        — Returns ProvisionState(blocks={}) if the file is absent.
        — Entries whose status is "running" are reset to "pending" (crash recovery).

    _save_state() -> None
        — Writes _state to _state_file as pretty-printed JSON (model_dump_json).
        — Called immediately after every status mutation.

    is_done(block_id: str) -> bool
        — Returns True iff _state.blocks[block_id].status == BlockStatus.done.

    pending(all_blocks: list[ResolvedBlock]) -> list[ResolvedBlock]
        — Returns blocks from all_blocks whose resolved_id is NOT done.
        — Preserves the DAG-resolved order.

    mark_running(block_id: str) -> None
        — Sets _state.blocks[block_id] = BlockRecord(status=running) and saves.

    mark_done(block_id: str, outputs: dict[str, Any]) -> None
        — Sets _state.blocks[block_id] = BlockRecord(status=done, outputs=outputs) and saves.

    mark_failed(block_id: str, error: str) -> None
        — Sets _state.blocks[block_id] = BlockRecord(status=failed, error=error) and saves.

    restore_context(context: ExecutionContext) -> None
        — For every block whose status == done, calls context.set_outputs(block_id, record.outputs).
        — Enables downstream blocks to wire from already-completed upstream blocks on a resumed run.
```

---

## Module: `provision/__init__.py`

```
from .progress import ProvisionProgress
from .state import BlockStatus, BlockRecord, ProvisionState

__all__ = ["ProvisionProgress", "BlockStatus", "BlockRecord", "ProvisionState"]
```

---

## Module: `provisioner.py` (complete)

### Constructor change

Add `runner: BlockRunner` as a third argument. The facade is responsible for constructing `BlockRunner` with the correct bridges before calling `Provisioner`.

```
Provisioner
    __init__(folder: Path, block_repository: BlockRepository, runner: BlockRunner) -> None
        _folder:     Path
        _repository: BlockRepository
        _resolver:   DAGResolver   (constructed internally, stateless)
        _runner:     BlockRunner
```

### `provision(block_refs: list[BlockRef]) -> None` — full algorithm

```
1. Guard: raise ValueError if block_refs is empty.

2. Load contracts
   blocks_ids = [BlockId(ref.resolved_id) for ref in block_refs]
   blocks     = {id: _repository.get_by_id(id) for id in blocks_ids}
   contracts  = {str(block.id): BlockContract.model_validate(block.contract)
                 for block in blocks.values()}

3. Resolve DAG
   resolved_blocks = _resolver.resolve(block_refs, contracts)
   — Raises DAGError subclasses on structural violations; propagate as-is.

4. Initialise runtime state
   context  = ExecutionContext()
   progress = ProvisionProgress(_folder, resolved_blocks)

5. Restore context from prior run
   progress.restore_context(context)
   — No-op on a fresh run; replays done-block outputs on a resume.

6. Execute pending blocks in order
   for block in progress.pending(resolved_blocks):
       progress.mark_running(block.ref.resolved_id)
       try:
           _runner.run_one(block, context)
           outputs = context.get_all_outputs(block.ref.resolved_id)
           progress.mark_done(block.ref.resolved_id, outputs)
       except Exception as exc:
           progress.mark_failed(block.ref.resolved_id, str(exc))
           raise

   — On exception the state file is flushed (mark_failed calls _save_state),
     so re-running skips completed blocks and retries only the failed one.
```

---

## Module: `facade.py` — `provision_resources` wiring

The `Blocks` facade is the composition root. It assembles all parts before handing control to `Provisioner`.

```
provision_resources(block_refs: list[BlockRef], folder: Path,
                    secrets_bridge: SecretsBridge,
                    terraform_bridge: TerraformBridge,
                    project_path: Path | None = None) -> None

    runner     = BlockRunner(
                     work_dir=folder,
                     blocks_root=_repository.folder,
                     secrets_bridge=secrets_bridge,
                     terraform_bridge=terraform_bridge,
                     project_path=project_path,
                 )
    provisioner = Provisioner(folder, _repository, runner)
    provisioner.provision(block_refs)
```

The bridges are injected by the project's `provision` usecase, which assembles concrete implementations from `freeloader.shared.terraform` and `freeloader.secrets.ports.interface`.

---

## State file: `provision.json`

Written at `<folder>/provision.json`. Format (example after a partially successful run):

```json
{
  "blocks": {
    "docker/dockerfile":   {"status": "done",    "outputs": {},                                    "error": null},
    "gitlab/registry":     {"status": "done",    "outputs": {"image_path": "registry.../acme-api"}, "error": null},
    "coolify/project":     {"status": "done",    "outputs": {"project_uuid": "uuid-5a3b"},          "error": null},
    "coolify/app":         {"status": "failed",  "outputs": {},                                    "error": "Terraform error: 502 Bad Gateway"},
    "github/repo":         {"status": "pending", "outputs": {},                                    "error": null}
  }
}
```

On a fresh run the file does not exist. After the first block completes it is created. On resume, `pending` and `running` (crashed) entries are executed; `done` entries are skipped.

---

## Resumability contract

| Entry state on load | Treatment |
|---|---|
| `done` | Skipped; outputs restored into `ExecutionContext`. |
| `running` | Reset to `pending`; retried (crash recovery). |
| `pending` | Executed normally. |
| `failed` | Executed normally (retry on re-run). |

---

## Invariants

- `ProvisionProgress` is the single writer of `provision.json`. `Provisioner` and `BlockRunner` never access the file directly.
- `BlockRunner.run_one` writes outputs into `ExecutionContext` via `context.set_outputs`. `Provisioner` reads them back via `context.get_all_outputs` and hands them to `progress.mark_done` for persistence.
- `Provisioner` raises on the first failed block. Partial pipelines are resumable; the caller does not need to track which blocks completed.
- `BlockRunner` is stateless between blocks. `ExecutionContext` is the only mutable in-process accumulator.
