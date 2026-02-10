# Projects

Projects are your apps — the things you're deploying. Each project is a directory with a `freeloader.yaml` manifest.

## Commands

| Command | What it does |
|---------|-------------|
| `fl projects init` | Scan CWD, detect tech stack, generate `freeloader.yaml` |
| `fl projects init --full` | Same, but includes **all** config fields with defaults |
| `fl projects status` | Show provisioned blocks and their state |

## Init

```bash
cd my-app
fl projects init
```

Freeloader scans your project directory, detects the tech stack (Python/uv, Node/npm, Go, Rust, etc.), and generates a `freeloader.yaml` with sensible defaults.

### Minimal vs Full

By default, `init` only includes **required** config fields:

```yaml
# fl projects init
- use: dockerfile
  config: {}
```

With `--full`, every config field is included with its default value — so you can see all available knobs:

```yaml
# fl projects init --full
- use: dockerfile
  config:
    template: auto
    node_version: "22"
    python_version: "3.12"
    serve_with: nginx
```

## Manifest Reference

### `project`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | **required** | Project name. Used for state dir, Terraform workspace, and default config values. |
| `description` | string | `""` | Optional description. For your own reference. |
| `source_dir` | string | `"."` | Path to the project source code (relative to manifest). |

### `blocks[]`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `use` | string | **required** | Block name from the catalog (e.g. `github-repo`, `dockerfile`). |
| `id` | string | same as `use` | Override the block ID. Required when using the same block type twice. |
| `config` | dict | `{}` | Config values passed to the block. Keys must match the block's `config` fields. |

### Using the Same Block Twice

Set `id` to distinguish them:

```yaml
blocks:
- use: github-repo
  id: frontend-repo
  config:
    name: my-app-frontend

- use: github-repo
  id: backend-repo
  config:
    name: my-app-backend
```

## Status

```bash
fl projects status
```

Shows which blocks have been provisioned, their output count, last apply time, and any errors.
