<div align="center">

# 🍕 freeloader

**You have better things to do than deploy the same app for the 100th time.**

Pipeline composer for indie developers who'd rather ship code than babysit infrastructure.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## The Problem

You just vibe-coded something brilliant over the weekend. Now you need to deploy it. Here's what that looks like:

> 1. Create a GitHub repo
> 2. Create a GitLab project for the container registry (because free tier)
> 3. Generate a production Dockerfile for your stack
> 4. Write the GitHub Actions CI pipeline
> 5. Wire GitLab registry credentials as GitHub secrets
> 6. Write the docker-compose for the target
> 7. Set up the deployment target (Coolify? Render? A VPS you forgot about?)
> 8. Register the app in Coolify
> 9. Copy the deploy webhook URL
> 10. Paste it back into GitHub secrets
> 11. Push, wait, pray
> 12. Debug why the Dockerfile doesn't build
> 13. Fix the CI, push again
> 14. Realize you forgot to set `GITLAB_TOKEN`
> 15. Mass-copy `.env` values you already entered somewhere last month

And next weekend? **You'll do it all over again.**

## The Fix

```bash
cd my-brilliant-app
fl projects init
fl credentials add-provider github
fl credentials add-provider gitlab
fl pipeline up --yes
```

That's it. Go grab coffee. Freeloader handles the rest.

---

## What Is This

Freeloader is a local CLI that **composes a cross-provider deployment pipeline** from reusable blocks. It connects your code to the cloud — GitHub, GitLab, AWS, Coolify, whatever — without locking you into any single vendor.

Think of it as a pipeline LEGO set. Each block does one thing. You snap them together. Freeloader figures out the order, wires the outputs, and runs each block with the right engine.

```
github-repo ──→ gitlab-registry ──→ github-actions-ci
                      │                      │
                      ▼                      ▼
                dockerfile              coolify-app
```

No YAML oceans. No Helm charts. No 400-line Terraform files copy-pasted between projects.

---

## Quickstart

```bash
# Install
uv tool install freeloader       # or: pip install freeloader

# One-time: store provider tokens (encrypted locally)
fl credentials add-provider github
fl credentials add-provider gitlab

# Import your existing SSH hosts
fl hosts scan
fl hosts import all

# Deploy a project
cd my-app
fl projects init                 # detects stack, creates freeloader.yaml
fl pipeline plan                 # see what will happen
fl pipeline up                   # make it happen

# Generate files only (Dockerfile, CI config)
fl pipeline generate

# SSH into your machines
fl ssh pi
```

---

## Features

### 📦 [Projects](docs/projects.md) — Manage project lifecycle

```bash
fl projects init [--full]        # scan CWD, detect stack, generate manifest
fl projects status               # show provisioned blocks and their state
```

Use `--full` to include all config fields with defaults so you can see every available knob.

### 🔧 [Pipeline](docs/pipeline.md) — Plan and execute

```bash
fl pipeline plan                 # resolve DAG, show execution order
fl pipeline up [--yes]           # provision all blocks
fl pipeline down [--yes]         # destroy all provisioned resources
fl pipeline generate             # run generator blocks only
```

### 🔑 [Credentials](docs/credentials.md) — Secrets and providers

```bash
fl credentials add-provider <name>   # store provider credentials
fl credentials check <name>          # verify they're valid
fl credentials set <key> <value>     # store arbitrary secret
fl credentials list-secrets          # list stored keys
```

All secrets encrypted locally in `~/.freeloader/secrets.enc`. Your laptop is the control plane.

### 🖥️ [Hosts](docs/hosts.md) — SSH machine inventory

```bash
fl hosts scan                    # discover from ~/.ssh/config + keys
fl hosts import all              # import into freeloader inventory
fl hosts list                    # show all registered machines
fl hosts add pi 192.168.1.50    # register manually
fl hosts check                   # ping all, report reachability
fl ssh pi                        # just SSH into it
```

Global inventory — not tied to any project. Your machines are yours.

### 🧱 [Blocks](docs/blocks.md) — Browse the catalog

```bash
fl blocks list                   # show all available blocks
fl blocks list --layer build     # filter by layer
```

### 🛠️ [Custom Blocks](docs/custom-blocks.md) — Build your own

A block is a folder with a `block.yaml`. No plugin API. No package to publish.

```bash
mkdir -p ~/.freeloader/blocks/my-block
# Add block.yaml + (main.tf | handler.py | templates/)
fl blocks list                   # it's already available
```

Three runner types: **terraform**, **api** (HTTP + Python handler), **generator** (Jinja2 templates).

---

## Architecture

```
~/.freeloader/                    ← your control plane
  hosts.yaml                     ← SSH host inventory
  secrets.enc                    ← encrypted vault
  config.yaml                   ← global defaults
  blocks/                       ← custom blocks
  projects/                     ← per-project state + terraform workspaces

your-project/
  freeloader.yaml               ← project manifest (what to deploy)
  src/                          ← your code
```

**Blocks** are the atomic unit. Each has a contract (requires/provides) and a runner. Freeloader resolves them into a **DAG**, wires outputs to inputs, and executes in topological order.

**Runners** handle execution:

| Runner | Executes via | Use case |
|--------|-------------|----------|
| `terraform` | `terraform apply` | Infra, repos, registries |
| `api` | HTTP calls via `handler.py` | Coolify, Render, webhooks |
| `generator` | Jinja2 templates → files | Dockerfiles, CI configs |

**Layers** determine execution order:

```
infra → platform → source → registry → build → deploy → network → data → observe
```

---

## Built-in Blocks

| Block | Layer | Runner | What it does |
|-------|-------|--------|-------------|
| `aws-ec2` | infra | terraform | Provision an EC2 instance |
| `github-repo` | source | terraform | Create a GitHub repo + wire secrets |
| `gitlab-registry` | registry | terraform | Create GitLab project as container registry |
| `dockerfile` | build | generator | Generate production Dockerfile + .dockerignore |
| `github-actions-ci` | build | generator | Generate CI/CD workflow with test, build, deploy |
| `coolify-app` | deploy | api | Register app in your self-hosted Coolify |

Full config reference for each block: **[docs/blocks.md](docs/blocks.md)**

---

## Philosophy

- **Free tiers first.** GitHub for source, GitLab for registry, Coolify for hosting. Pay nothing until you need to.
- **Compose, don't configure.** Small blocks with typed contracts. Snap together, auto-wire.
- **Your laptop is the control plane.** Secrets encrypted locally. No SaaS dependency. No cloud dashboard.
- **Convention over ceremony.** Detect the stack, generate the files, provision the infra. Ask questions later.
- **Community-powered.** Creating a block is creating a folder. Share them, fork them, compose them.

---

## Development

```bash
git clone https://github.com/your-org/freeloader.git
cd freeloader
uv sync --dev
uv run pytest tests/ -x -q
```

---

## License

MIT — do whatever you want.

---

<div align="center">

**Stop deploying. Start freeloading.** 🍕

</div>
