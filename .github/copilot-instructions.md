# agentic

Start in the `agentic/` folder and stay anchored there while discovering project-specific operating guidance.

Treat these files as the primary operating contract for the project:

- `agentic/agentic.yaml`: durable project-state architecture agreement that the checker validates
- `agentic/rules/shared/`: reusable shared guidance mirrored from packaged resources
- `agentic/rules/local/`: the only local profile surface for repo-specific narrowing discovered in this project

When crafting or refining `agentic/agentic.yaml`:

- Treat it as durable project state, not temporary prompt scratch space.
- Derive tags from durable ownership seams such as features, modules, layers, adapters, or package boundaries that are likely to survive refactors.
- Prefer tags that classify many files consistently over one-off path matches that explain only a single exception.
- Start boundary rules broad at the seam level, then add narrow `allow` exceptions only for real public entrypoints, shims, or integration seams.
- Use `allow_same_match` when files sharing the same owner tag should be allowed to collaborate internally.
- Add `flow` only when the repository has a stable layered, onion, or directional dependency model worth checking across many files.
- Keep exclusions limited to generated code, vendored code, temporary tooling surfaces, or other paths that should not participate in the architecture map.
- Reuse facts already captured under `agentic/rules/local/` when choosing names, seams, and exceptions; do not invent a second local policy surface.

Compact authoring sequence:

1. Identify the stable seams that deserve tags.
2. Add the smallest tag set that explains those seams clearly.
3. Add boundary rules for the important ownership constraints.
4. Add narrow `allow` exceptions only where the public seam is intentional.
5. Add `flow` only if directional architecture is real and stable.
6. Add exclusions last, and keep them narrow.

Do not spread local contract decisions across ad hoc folders or unrelated docs when they belong in `agentic/`.
