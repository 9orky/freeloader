# Plan: Reduce secrets feature code bloat

## TL;DR
The refactor introduced 3 unnecessary layers: 7 individual usecase files (each 3–10 lines delegating to `load_storage`), a `password` parameter threaded through all public API layers, and CLI retry/prompt logic that contradicts the design (passwords always come from the session file in FREELOADER_HOME). The reduction is: collapse usecases into application.py, strip the password param from the public API, and remove the CLI retry helpers.

## Key findings
- `usecases/` has 7 files, each is 3–10 lines calling `load_storage(password=password).one_method()`
- `application.py` is a thin re-export of those 7 functions — same signatures
- `password` param flows: cli → application → usecases → load_storage — but `SecretSession` already reads it from disk
- `_with_password_retry` + `_prompt_password` in `cli.py` contradict the design contract ("only rely on stored session")
- `storage/models.py` defines `StoredSecret` which is unused
- `models.py` just has `SecretEntry = Secret` alias + `SecretMutationResult`

## Steps

### Phase 1 — Remove `usecases/` layer
1. Move all 7 usecase function bodies directly into `application.py` (drop `password` param from each)
2. Delete `usecases/` directory (8 files: 7 modules + `__init__.py`)

### Phase 2 — Strip `password` param from public API
3. `application.py`: remove `password` from all 7 function signatures; call `load_storage()` with no args
4. `ports/interface.py`: remove `password=None` from all `application.*` call sites
5. Verify `storage/__init__.py::load_storage` signature stays intact (it reads session internally)

### Phase 3 — Simplify CLI
6. `cli.py`: remove `_with_password_retry`, `_prompt_password`, `PasswordRequiredError` import
7. Replace retry lambdas with direct `application.*` calls; `PasswordRequiredError` bubbles up as an error via `@console.handle_errors`

### Phase 4 — Storage cleanup
8. `storage/models.py`: remove unused `StoredSecret` dataclass

### Phase 5 — Test updates
9. `test_secrets_feature.py`: update tests that monkeypatch `password` param or test retry flow
   - `test_secrets_cli_prompts_for_vault_password_only_in_cli` → remove (tests deleted behavior)
   - `test_secrets_port_reads_via_application_and_normalizes_names` → remove `password` assertions
   - `test_secrets_port_writes_values_via_application_in_one_call` → remove `password` assertions
   - `test_secrets_cli_add_calls_application_and_renders_result` → remove `password` assertions
   - `test_secrets_cli_reuses_password_saved_in_freeloader_home` → remove vault-pass from `input=`, pre-populate session file instead
   - `test_secrets_storage_reads_legacy_session_password_file` → keep as-is (tests storage layer directly)

## Relevant files
- `src/freeloader/secrets/application.py` — rewrite: inline usecase logic, drop `password` param
- `src/freeloader/secrets/usecases/` — delete entire directory (8 files)
- `src/freeloader/secrets/cli.py` — remove retry helpers, use direct calls
- `src/freeloader/secrets/ports/interface.py` — remove `password` args from calls
- `src/freeloader/secrets/storage/models.py` — remove `StoredSecret`
- `tests/test_secrets_feature.py` — update 5 tests

## Verification
1. `pytest tests/test_secrets_feature.py` passes with no skips
2. `pytest tests/` passes (no regressions in other features)
3. `ruff check src/freeloader/secrets/` clean
4. Manual: `fl secrets ls` in env with populated `vault-password` file — no password prompt, lists secrets

## Decisions
- Password param removal does NOT affect `storage/__init__.py::load_storage` — it keeps its optional `password` param for the initial vault-setup path (env var or session migration)
- `StoredSecret` removed — confirmed not imported anywhere outside `storage/models.py`
- `models.py` kept as-is — `SecretEntry` alias and `SecretMutationResult` are part of the public API
- **Test-only code rule**: if any symbol, parameter, or module exists solely because a test references it (and not for real production use), it must be removed from production code and the test updated to stop relying on it
