# Block Provision Progress Design

## Problem

`fl project provision` is currently silent until the whole provisioning flow finishes.
The user gets one final success or failure message, but cannot see:

- whether block resolution already started
- which block is currently being prepared or applied
- whether the process is still alive during long Terraform runs
- which block/phase failed

The existing implementation already has meaningful execution phases inside the
block feature:

1. build a DAG plan
2. prepare all block workspaces with `dump_assets -> init -> plan`
3. apply blocks in dependency order
4. for blocks with dependency inputs, re-run `init -> plan`
5. collect outputs into the final report

That makes progress reporting a good fit for domain events emitted by the block
provisioning service and consumed by the project CLI.

## Goals

- Show immediate feedback when provisioning starts.
- Show the current block and phase while the process is running.
- Preserve the current architecture: block owns provisioning orchestration, project
	owns user presentation.
- Keep the current blocking `provision()` and `destroy()` APIs available for callers
	that only care about the final report.
- Make failures visible with block and phase context.

## Non-goals

- Streaming raw Terraform stdout as part of the first iteration.
- Changing the Terraform execution model to async or concurrent applies.
- Reworking block resolution or Terraform runner internals beyond what is needed to
	surface coarse-grained progress.

## Proposed Design

Detailed implementation breakdowns:

- `PROGRESS_STEP_1.md` - block feature event model and generator-based orchestration
- `PROGRESS_STEP_2.md` - project feature forwarding and CLI integration
- `PROGRESS_STEP_3.md` - shared console progress rendering helper and dedicated UI support file

### 1. Add block domain events

Introduce feature-local event models under the block domain, for example in
`src/freeloader/block/domain/events.py`.

Use frozen dataclasses and keep them focused on meaningful business milestones,
not low-level subprocess details.

Recommended event set for provisioning:

- `ProvisioningStarted(total_blocks, block_ids)`
- `BlockPreparationStarted(block_id, index, total)`
- `BlockPreparationCompleted(block_id, index, total)`
- `BlockApplyStarted(block_id, index, total, has_dependency_inputs)`
- `BlockDependencyInputsStarted(block_id, index, total, provider_ids)`
- `BlockApplyCompleted(block_id, index, total, outputs)`
- `ProvisioningFailed(block_id, phase, error)`
- `ProvisioningFinished(report)`

Recommended event set for destroy:

- `DestroyStarted(total_blocks, block_ids)`
- `BlockDestroyStarted(block_id, index, total)`
- `BlockDestroyCompleted(block_id, index, total)`
- `BlockDestroyFailed(block_id, index, total, error)`
- `DestroyFinished(report)`

Notes:

- `ProvisioningFinished` and `DestroyFinished` may carry the existing report
	objects only if those report models live in a lower layer owned by block runtime
	semantics, not in `application/`. A domain event must not import an
	application-layer model.
- `ProvisioningFailed` should identify both the block and the phase (`prepare`,
	`dependency_inputs`, `apply`) so the UI can show an actionable error.
- Keep event payloads small. Do not put Terraform stdout into the domain event in
	the first iteration.

### 2. Add a generator-based service API on the block side

Add streaming methods to the block provisioning service:

- `BlockProvisioningService.provision_events(...) -> Iterator[BlockProvisionEvent]`
- `BlockProvisioningService.destroy_events(...) -> Iterator[BlockDestroyEvent]`

Behavior:

- The generator yields events immediately before and after each meaningful phase.
- The generator yields the terminal `...Finished(report)` event on success.
- On failure, it yields `ProvisioningFailed(...)` and then re-raises the exception.

Keep the current non-streaming methods as thin wrappers:

- `provision(...)` drains `provision_events(...)`, captures the terminal report, and
	returns the existing `ProvisioningReport`.
- `destroy(...)` drains `destroy_events(...)`, captures the terminal report, and
	returns the existing `DestroyReport`.

This keeps backward compatibility while making progress available to callers that
want it.

### 3. Thread the stream through the public block API

Expose the new stream at the block application boundary.

Recommended additions:

- `block/application/commands.py`
	- `provision_blocks_events(...)`
	- `destroy_blocks_events(...)`
- `block/application/interface.py`
	- `Blocks.provision_events(...)`
	- `Blocks.destroy_events(...)`

To keep the cross-feature boundary clean, re-export the event types from the block
package root together with the existing public facade.

That lets the project feature depend on block progress through the block package's
public API instead of importing deep internal modules.

### 4. Present block events on the project side

Extend the project-side gateway to forward the generator instead of hiding it.

Recommended additions:

- `project/domain/repository.py`
	- add `provision_events(...)`
	- add `destroy_events(...)`
- `project/infrastructure/block_gateway.py`
	- forward to `Blocks.for_project(...).provision_events(...)`
	- forward to `Blocks.for_project(...).destroy_events(...)`
- `project/application/commands.py`
	- add `provision_project_events(folder)`
	- add `forget_project_events(folder)`

Keep the existing `provision_project()` and `forget_project()` as compatibility
wrappers that fully drain the generator.

This preserves the architectural split:

- block decides what happened
- project decides how to show it to the user

### 5. Add project-side live presentation

The project CLI should consume the event generator and render progress in real time.

Recommended behavior for `fl project provision`:

- start a Rich status spinner immediately after manifest loading
- update the status text whenever a new event arrives
- print durable completion lines for completed blocks
- stop the spinner and print a clear failure line if an exception occurs
- print the existing final success line after `ProvisioningFinished`

Suggested status text mapping:

- `ProvisioningStarted` -> `Resolving and preparing N blocks...`
- `BlockPreparationStarted` -> `Preparing i/N: <block_id>`
- `BlockApplyStarted` -> `Applying i/N: <block_id>`
- `BlockDependencyInputsStarted` -> `Resolving dependency inputs for i/N: <block_id>`
- `BlockApplyCompleted` -> `Applied i/N: <block_id>`
- `ProvisioningFailed` -> `Failed during <phase>: <block_id>`

Important UX detail:

The current Terraform runner blocks inside `init`, `plan`, and `apply`, so the first
iteration will not show line-by-line Terraform output. The spinner still solves the
main user problem because the terminal no longer looks frozen. The user will see the
current phase and block while waiting.

### 6. Failure semantics

Failure handling should be explicit and deterministic:

- if preparation fails, emit `ProvisioningFailed(block_id, "prepare", error)`
- if dependency-input binding fails, emit `ProvisioningFailed(block_id, "dependency_inputs", error)`
- if apply fails, emit `ProvisioningFailed(block_id, "apply", error)`
- re-raise after emitting the failure event so the existing CLI error handling still
	exits non-zero

This preserves the current error path while giving the UI one last meaningful event
to display.

## Implementation Plan

1. Add block progress event models and event union aliases.
2. Refactor `BlockProvisioningService` to expose generator methods and keep current
	 report-returning methods as wrappers.
3. Expose the stream through block application commands and the `Blocks` facade.
4. Extend the project block gateway and project application commands with streaming
	 variants.
5. Add a small console helper or direct Rich `status` usage in the project CLI to
	 render the event stream live.
6. Mirror the same pattern for `forget` so destroy is not silent either.

## Test Plan

Add or update tests at these levels:

- block service: event order for a normal two-block dependency flow
- block service: failure event emitted before exception is raised
- block application commands: streaming methods wire repository, runner, and service
- project gateway: forwards streaming calls to the block facade
- project CLI: renders progress messages while consuming the event stream

The most important assertion is event ordering. The stream must match the real
execution order already verified by `tests/test_block_provisioner.py`.

## Acceptance Criteria

The plan is acceptable when all of the following are true:

- `fl project provision` shows progress immediately instead of staying silent.
- The user can always see which block is currently being prepared, having dependency inputs resolved, or
	applied.
- A failure identifies both the block and the phase that failed.
- The block feature remains the source of provisioning truth; project only presents
	the events.
- Existing synchronous APIs keep working for callers that only want the final report.
- The same approach is available for destroy/forget, even if it is implemented right
	after provision in a second commit.

## Optional Later Improvement

If coarse-grained phase updates are not enough, a later iteration can add
infrastructure-level streaming from `TerraformRunner` using `subprocess.Popen` and
translate that into richer events. That should be a separate step. It is not needed
to solve the current "silent wait" problem.
