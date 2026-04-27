# Freeloader Agent Entry

Start with [docs/AGENT.md](docs/AGENT.md), then read [.agentic/rules/local/INDEX.md](.agentic/rules/local/INDEX.md) for repo-specific operating rules.

The short version:

- Freeloader is a Python 3.12+ CLI. Use `uv run ...` for validation.
- Features live under `src/freeloader/<feature>/` and follow `domain -> infrastructure -> application -> ui` dependency direction.
- Cross-feature calls go through feature package roots only, such as `freeloader.block.Blocks`.
- Keep `project` as the composition/planning owner. Keep `block`, `service_providers`, `secrets`, and `shared.tech` focused on their own facts and capabilities.
- Before changing architecture, check [.agentic/agentic.yaml](.agentic/agentic.yaml), [docs/FEATURE_ARCHITECTURE.md](docs/FEATURE_ARCHITECTURE.md), and `tests/architecture_rules/`.
