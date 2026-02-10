# Blocks

Blocks are the atomic unit of Freeloader. Each block is a self-contained, reusable piece of infrastructure work with a typed contract: what it requires, what it provides, and which runner executes it.

## Commands

| Command | What it does |
|---------|-------------|
| `fl blocks list` | Show all available blocks |
| `fl blocks list --layer build` | Filter by layer |

## The Block Model

```yaml
# block.yaml
block:
  name: github-repo
  runner: terraform
  layer: source
  provider: github
  required_secrets: [GITHUB_TOKEN]

provides:
  source.repo_name: { type: string }
  source.clone_url: { type: string }

requires:
  registry.token: { optional: true, usage: github_secret }
```

Freeloader resolves all blocks into a **DAG** at plan time. Outputs from upstream blocks are automatically wired as inputs to downstream blocks. No manual plumbing.

## Runners

| Runner | Executes via | State | Use case |
|--------|-------------|-------|----------|
| **terraform** | `terraform apply` | Terraform state | Infra, repos, registries |
| **api** | HTTP calls | Freeloader state | Coolify, Render, webhooks |
| **generator** | Jinja2 templates → files | Idempotent files | Dockerfiles, CI configs |

## Layers

Blocks are organized into logical layers that determine execution order:

```
infra → platform → source → registry → build → deploy → network → data → observe
```

## Built-in Blocks

| Block | Layer | Runner | What it does |
|-------|-------|--------|-------------|
| `aws-ec2` | infra | terraform | Provision an EC2 instance |
| `github-repo` | source | terraform | Create a GitHub repository + wire secrets |
| `gitlab-registry` | registry | terraform | Create a GitLab project as container registry |
| `dockerfile` | build | generator | Generate production Dockerfile + .dockerignore |
| `github-actions-ci` | build | generator | Generate CI/CD workflow with test, build, deploy |
| `coolify-app` | deploy | api | Register app in your self-hosted Coolify instance |

## Block Config Reference

### `github-repo` — terraform · source

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | **required** | Repository name |
| `org` | string | — | GitHub organization (omit for personal repos) |
| `visibility` | string | `"private"` | `public` or `private` |
| `description` | string | `""` | Repository description |
| `protect_main` | boolean | `false` | Enable branch protection on `main` |

Secrets: `GITHUB_TOKEN` · Provides: `source.repo_name`, `source.clone_url`

### `gitlab-registry` — terraform · registry

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | **required** | GitLab project name |
| `visibility` | string | `"private"` | `public`, `private`, or `internal` |
| `description` | string | `""` | Project description |
| `token_scopes` | list | `[read_registry, write_registry]` | Access token scopes |

Secrets: `GITLAB_TOKEN` · Provides: `registry.host`, `registry.token`, `registry.user`, `registry.image_path`, `registry.project_id`

### `aws-ec2` — terraform · infra

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| `instance_type` | string | `"t3.micro"` | EC2 instance type (`t2.micro`, `t3.micro`, `t3.small`) |
| `region` | string | `"eu-central-1"` | AWS region |
| `ami` | string | `""` | AMI ID (auto-detected if empty) |
| `key_name` | string | **required** | SSH key pair name |
| `ssh_public_key` | string | **required** | Public key content |

Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` · Provides: `server.ip_address`, `server.instance_id`, `server.ssh_user`, `server.public_dns`

### `dockerfile` — generator · build

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| `template` | string | `"auto"` | Template name or `auto` for stack detection |
| `node_version` | string | `"22"` | Node.js version (for JS/TS stacks) |
| `python_version` | string | `"3.12"` | Python version (for Python stacks) |
| `serve_with` | string | `"nginx"` | Production server: `nginx`, `node`, or `none` |

No secrets required. No provides/requires — pure file generation.

### `github-actions-ci` — generator · build

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| `test_command` | string | `"npm test"` | Test command to run in CI |
| `build_platforms` | list | `["linux/amd64"]` | Docker build platforms |
| `node_version` | string | `"22"` | Node.js version for CI runner |

Requires: `source.repo_name`, `registry.host`, `registry.image_path`, optionally `deploy.webhook_url`

### `coolify-app` — api · deploy

Registers an app in your **self-hosted** Coolify instance. Coolify runs on your own server — this block talks to its API to create the application and get a deploy webhook.

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| `app_name` | string | **required** | Application name in Coolify |
| `server_uuid` | string | **required** | UUID of your server in Coolify. Find it in: Dashboard → Servers → click your server → UUID is in the URL. |
| `coolify_url` | string | **required** | Base URL of your Coolify instance (e.g. `https://coolify.example.com`) |
| `project_uuid` | string | `""` | Coolify project UUID (omit to use default project) |
| `environment` | string | `"production"` | Coolify environment name |
| `ports` | string | `"80"` | Ports to expose (comma-separated) |
| `domain` | string | `""` | Custom domain for the app (e.g. `app.example.com`) |

Secrets: `COOLIFY_TOKEN` (generate at Coolify → Keys & Tokens → API Tokens)
Requires: `registry.image_path`, `registry.user`, `registry.token`
Provides: `deploy.webhook_url`, `deploy.app_url`, `deploy.app_uuid`

## Provides/Requires Namespaces

The naming convention is `namespace.key`. These are the common namespaces:

| Namespace | Typical keys |
|-----------|-------------|
| `server` | `ip_address`, `instance_id`, `ssh_user`, `public_dns` |
| `source` | `repo_name`, `clone_url` |
| `registry` | `host`, `token`, `user`, `image_path`, `project_id` |
| `platform` | `api_url`, `api_token` |
| `deploy` | `webhook_url`, `app_url`, `app_uuid` |
| `dns` | `record_id`, `fqdn` |

You can invent your own namespaces. As long as one block provides `foo.bar` and another requires `foo.bar`, they'll be wired together.
