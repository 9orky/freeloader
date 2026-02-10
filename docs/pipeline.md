# Pipeline

The pipeline is the core of Freeloader — it takes your `freeloader.yaml`, resolves the dependency graph, and runs each block in order.

## Commands

| Command | What it does |
|---------|-------------|
| `fl pipeline plan` | Resolve the DAG and show execution order |
| `fl pipeline up` | Provision all blocks (add `--yes` to skip confirmation) |
| `fl pipeline down` | Destroy all provisioned resources |
| `fl pipeline generate` | Run generator blocks (Dockerfile, CI, etc.) only |

## How It Works

1. **Parse** — reads `freeloader.yaml` and loads each block's contract from the catalog
2. **Resolve** — builds a DAG from provides/requires, wires outputs → inputs
3. **Group** — splits blocks by runner type (terraform, api, generator)
4. **Execute** — runs each group in topological order

```
fl pipeline plan

┌──────────────────────────────────────────────┐
│ Execution Plan: my-app                       │
├─────────────────┬────────┬───────────┬───────┤
│ Block           │ Layer  │ Runner    │ Deps  │
├─────────────────┼────────┼───────────┼───────┤
│ github-repo     │ source │ terraform │ —     │
│ gitlab-registry │ reg.   │ terraform │ —     │
│ dockerfile      │ build  │ generator │ —     │
│ gh-actions-ci   │ build  │ generator │ 1,2   │
│ coolify-app     │ deploy │ api       │ 2     │
└─────────────────┴────────┴───────────┴───────┘
```

## Generate Only

If you just need files (Dockerfile, CI config) without provisioning infrastructure:

```bash
fl pipeline generate
```

This runs only `generator` blocks. No Terraform, no API calls. Safe to run anytime.

## Destroy

```bash
fl pipeline down
```

Tears down everything in reverse order. Terraform resources get `terraform destroy`, API resources get their `destroy()` handler called, generated files get deleted.
