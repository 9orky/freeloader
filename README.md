# freeloader

You have better things to do than deploy the same app for the hundredth time.

`freeloader` is a Python CLI for composing deployment infrastructure from reusable Terraform-backed blocks. It is built for solo builders and small teams who want a repeatable path from a local project to hosted code, CI, container registry, and deployment targets without re-writing the same glue every weekend.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## What It Does

Freeloader turns deployment setup into a manifest-driven planning flow:

1. Detect the project stack.
2. Inspect available infrastructure blocks.
3. Check local provider support and required secrets.
4. Generate a manifest of selected blocks.
5. Provision or destroy resources through the block execution layer.

Blocks are small Terraform-backed units. A block declares its config, requirements, provided outputs, costs, and assets. The project planner decides which blocks fit the current project and can explain why a block was excluded.

## Install

```bash
pipx install freeloader
```

or:

```bash
uv tool install freeloader
```

The CLI entrypoint is:

```bash
fl --help
```

## Quick Start

From inside a project directory:

```bash
fl project detect
fl project manage --explain
fl project provision
```

Useful commands:

```bash
fl project status
fl secrets ls
fl service-providers --help
```

## Concepts

### Project

The `project` feature owns composition. It detects the tech stack, asks the block catalog for candidates, evaluates provider support and secret availability, and writes the manifest.

### Blocks

Blocks are validated Terraform definition units. Each block lives with its `block.yml`, `main.tf`, and optional templates. Contracts use shared `requires` and `provides` port names documented in [`docs/BLOCK_PORT_CONTRACTS.md`](docs/BLOCK_PORT_CONTRACTS.md).

### Service Providers

Service providers own provider identity, auth, billing checks, and local support checks. Provider capability is reported as structured data so planning can explain unsupported blocks.

### Secrets

Secrets are stored behind the `secrets` feature. Planning only checks key availability; secret values do not leave the secrets boundary.

## Development

This project uses Python 3.12+, `uv`, `pytest`, `ruff`, and Hatchling.

```bash
uv sync --all-groups
uv run pytest
uv run ruff check
```

Build locally:

```bash
uv run python -m build
uv run twine check dist/*
```

## Releases

The package version is derived from the GitHub release tag. Create tags like:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The `release.yml` workflow builds the package from the tag and publishes to PyPI with trusted publishing. Configure a PyPI trusted publisher for:

- Repository: `9orky/freeloader`
- Workflow: `release.yml`
- Environment: `pypi`

## Status

Freeloader is pre-1.0 software. Expect the block catalog and planning diagnostics to evolve quickly while the public CLI stabilizes.
