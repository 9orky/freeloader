# Block System — Block Definition (`block.yml`)

## Overview

`block.yml` is the metadata contract of a block. It describes:
- what the block provides (output ports).
- what the block requires (input ports wired from other blocks' outputs).
- what layer the block belongs to.
- which configuration fields the user can set.
- which variables must be fetched from the secret vault.

It does **not** repeat what `main.tf` already defines (resource type, provider). It bridges `main.tf` and the provisioning system.

---

## Term Reference

### Layer

A **Layer** is a semantic category assigned to every block. It describes *what role* the block plays and provides a coarse execution ordering that the DAG uses as a secondary sort key (after explicit port dependencies).

```python
class Layer(str, Enum):
    infra    = "infra"
    platform = "platform"
    source   = "source"
    registry = "registry"
    build    = "build"
    deploy   = "deploy"
    network  = "network"
    data     = "data"
    observe  = "observe"
```

Natural execution order from coarsest to finest: `infra → platform → source → registry → build → deploy → network → data → observe`.

The layer order is a **tie-breaker**. The port dependency graph (DAG edges from `requires`/`provides`) always takes precedence. A `source`-layer block that requires a port from a `registry`-layer block will be placed after the registry block, overriding the naive layer order.

#### Block–Layer Mapping (existing blocks)

| Block                  | Layer      |
|------------------------|------------|
| `aws/ec2`              | `infra`    |
| `coolify/project`      | `platform` |
| `git/gitignore`        | `source`   |
| `git/local_repo`       | `source`   |
| `docker/dockerfile`    | `source`   |
| `docker/dockerignore`  | `source`   |
| `github/repo`          | `source`   |
| `gitlab/registry`      | `registry` |
| `github/actions_ci`    | `build`    |
| `coolify/app`          | `deploy`   |
| `coolify/service`      | `deploy`   |

---

### Port

A **Port** is a named data slot used to connect blocks. Ports come in two kinds:

#### `provides`
Outputs the block makes available after it runs. These are direct mappings to Terraform `output` values in `main.tf`.

```yaml
provides:
  host:
    description: Container registry hostname.
  image_path:
    description: Full image path including namespace.
  token:
    description: Registry access token.
    sensitive: true
```

#### `requires`
Inputs the block needs, which must be satisfied by a `provides` port from another block in the same pipeline.

```yaml
requires:
  registry.image_path:
    description: Image path used to configure the deployment.
  registry.token:
    description: Registry token stored as a repo secret.
    optional: true
```

Port keys in `requires` use **namespaced notation**: `{layer}.{output_name}`. The DAG resolver matches by key — exactly one block in the pipeline must provide a matching key. If two blocks provide the same key, the resolver raises `AmbiguousProvider`. If a required (non-optional) key is missing, it raises `MissingRequirement`.

#### `PortSpec` fields

| Field         | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `description` | string | no       | Human-readable explanation of the port's value.  |

| `optional`    | bool   | no       | If `true`, the block runs even if unconnected.   |
| `sensitive`   | bool   | no       | Value is masked in logs and manifest output.     |

---

### Config Field

**Config fields** are user-facing variables that come from the project manifest rather than from another block's port. They map to Terraform input `variable` blocks in `main.tf`.

Config fields are split into two visibility groups:

#### `basic`
Variables the user is expected to set for every project. They appear prominently in the manifest and CLI output.

#### `advanced`
Variables with sensible defaults that power users can override. Hidden from the manifest by default; shown with a `--full` flag.

#### Combined `secrets` annotation
Variables that must be fetched from the secret vault. Declaring them here tells the provisioner to retrieve the value at runtime rather than ask the user for it in plain text. Secrets are never written to `freeloader.yaml`.

```yaml
config:
  basic:
    - name: name
      description: Project name. Used as the repository name.
      required: true

    - name: visibility
      description: Repository visibility.
      default: private
      choices: [private, public]

  advanced:
    - name: protect_main
      description: Enable branch protection on the main branch.
      default: false

  secrets:
    - name: github_token
      description: GitHub personal access token with repo scope.
```

---

## Full `block.yml` Schema

```yaml
# block.yml — complete annotated example (gitlab/registry)

block:
  description: Creates a GitLab project and returns registry credentials.
  layer: registry        # Semantic category; see Layer table above.

# Ports this block exports after a successful apply.
provides:
  host:
    description: Container registry hostname (registry.gitlab.com).
  user:
    description: Registry username (oauth2 for token auth).
  token:
    description: Registry access token.
    sensitive: true
  image_path:
    description: Full image path including namespace.
  project_id:
    description: GitLab project numeric ID.

# Ports this block needs from other blocks. Empty for gitlab/registry.
requires: {}

# User-facing configuration fields mapped to main.tf variables.
config:
  basic:
    - name: name
      description: GitLab project name and registry namespace.
      required: true

    - name: visibility
      description: Project visibility.
      default: private
      choices: [private, public]

  advanced:
    - name: token_scopes
      description: Access token scopes granted to freeloader.
      default: [read_registry, write_registry]

  secrets:
    - name: gitlab_token
      description: GitLab personal access token with API scope.
```

---

## Another Example: `coolify/app`

```yaml
block:
  description: Deploys a Docker image application on a Coolify server.
  layer: deploy

provides:
  app_uuid:
    description: Internal UUID assigned by Coolify.
  app_url:
    description: Public URL of the deployed application.

requires:
  registry.image_path:
    description: Full Docker image reference to deploy.
  platform.project_uuid:
    description: Coolify project under which the app is created.

config:
  basic:
    - name: name
      description: Application name.
      required: true
    - name: domain
      description: Custom domain for the application.
      default: ""

  advanced:
    - name: environment_name
      description: Coolify environment name.
      default: production
    - name: docker_registry_image_tag
      description: Image tag to deploy.
      default: latest
    - name: ports_exposes
      description: Ports exposed by the container.
      default: "80"
    - name: server_uuid
      description: UUID of the target Coolify server.
    - name: destination_uuid
      description: UUID of the Coolify network destination.

  secrets:
    - name: coolify_token
      description: Coolify API token.
    - name: coolify_endpoint
      description: Coolify API base URL.
```

---

## Multi-pass Dependency: `github/repo` and Registry Secrets

`github/repo` optionally stores registry credentials as GitHub Actions secrets. It also optionally stores a `deploy_webhook_url` from the deploy-target block.

These are declared as optional `requires` ports:

```yaml
requires:
  registry.host:
    optional: true
  registry.user:
    optional: true
  registry.token:
    optional: true
    sensitive: true
  registry.image_path:
    optional: true
  deploy.webhook_url:
    optional: true
    sensitive: true
```

When these ports are connected, the DAG matches each requires key against the `provides` of all other blocks in the pipeline and places the providers before `github/repo`, overriding the naive layer order. The repo is created last so it can receive all secrets in a single apply.

Requires keys use **namespaced notation**: `{layer}.{output_name}`. The dot is replaced with an underscore when deriving the corresponding Terraform variable name (e.g. `registry.image_path` → variable `registry_image_path`). This means the naming in `block.yml` `requires` and in `main.tf` variables must be consistent.
