# Block System — Abstract

## What Is a Block?

A **Block** is a thin, self-contained wrapper around a Terraform module. Each block encapsulates a single infrastructure or asset concern (e.g., a GitHub repository, a GitLab image registry, an AWS EC2 instance, a Dockerfile).

Blocks live at:
```
src/freeloader/blocks/{provider}/{block_name}/
```

## The Problem

Building a complete deployment pipeline requires many interdependent resources. Some values come from user configuration; others are only available as outputs from previously created resources. Managing this manually means:

- Copy-pasting credentials and identifiers between steps.
- Knowing the exact creation order by heart.
- Re-running steps when something changes upstream.

## The Solution

Each block declares:
- **what it provides** — named output ports (e.g., `image_path`, `clone_url`).
- **what it requires** — named input ports that must be satisfied by another block's output.
- **which layer it belongs to** — a semantic category that determines ordering.

A **DAG resolver** reads these declarations, wires outputs to inputs, and produces a deterministic, ordered execution plan. The user only picks which blocks to use; the system figures out the rest.

## Block Composition Example

A typical pipeline might include:

| Block              | Layer      | Provides                         | Requires             |
|--------------------|------------|----------------------------------|----------------------|
| `docker/dockerfile`| `source`   | *(local file, no ports)*         | —                    |
| `gitlab/registry`  | `registry` | `host`, `token`, `image_path`    | —                    |
| `github/repo`      | `source`   | `clone_url`                      | `registry.*`         |
| `coolify/project`  | `platform` | `project_uuid`                   | —                    |
| `coolify/app`      | `deploy`   | `app_uuid`, `app_url`            | `registry.*`, `platform.*`, `infra.*` |

The system resolves dependencies and produces execution steps in the right order — no manual wiring needed.

## Two Artefacts per Block

| File        | Purpose                                              |
|-------------|------------------------------------------------------|
| `main.tf`   | Terraform code — the actual resource definition.     |
| `block.yml` | Metadata — ports, layer, config, secrets declaration.|

`main.tf` is the SSOT for what the block does. `block.yml` is the SSOT for how it connects.
