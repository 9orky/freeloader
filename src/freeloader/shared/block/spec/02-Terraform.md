# Block System — Terraform Best Practices (`main.tf`)

## Principle: Terraform Is the Only Runtime

All blocks — whether they create a cloud resource or a local file — use Terraform as their execution engine. There is no separate runner for local assets. This keeps the toolchain uniform and gives all blocks:
- state tracking (`terraform.tfstate`)
- idempotent apply/destroy
- consistent variable injection

Local file generation uses the `local` provider (`local_file` resource) or `terraform_data` with `local-exec`.

---

## File Structure

Every `main.tf` follows this section order:

```hcl
# 1. Provider requirements (only when a remote provider is needed)
terraform {
  required_providers { ... }
}

# 2. Input variables — declared individually, never as a big map
variable "name" { ... }

# 3. Locals — computed values, endpoint normalization, templates
locals { ... }

# 4. Provider configuration
provider "..." { ... }

# 5. Resources
resource "..." "..." { ... }

# 6. Outputs — every value another block may need
output "..." { ... }
```

---

## Variables

### Split by concern

| Concern       | Rule                                                                   |
|---------------|------------------------------------------------------------------------|
| **Identity**  | `name` is always basic and always required. No default.                |
| **Secrets**   | Mark with `sensitive = true`. Never assign a hard-coded default.       |
| **Behaviour** | Provide a sensible default. Mark advanced in `block.yml`.              |
| **Wired**     | Values passed from another block's output. Declare with no default (required) in `main.tf`; the wiring is handled by the block system, not the user. |

### Validation

Always add `validation` blocks for:
- Paths (`direxists`, `fileexists`)
- URLs (`can(regex(...))`)
- Enum-like strings (list of supported values)

```hcl
# Good: catches mistakes early, gives a clear error message
variable "language" {
  type    = string
  default = "python"
  validation {
    condition     = contains(["python", "node", "go"], var.language)
    error_message = "Unsupported language '${var.language}'. Choose python, node, or go."
  }
}
```

### Sensitive variables

```hcl
variable "coolify_token" {
  type      = string
  sensitive = true
  # No default — secrets are always injected at runtime from the vault
}
```

---

## Locals

Use `locals` for:
- Any value derived from two or more variables (avoid repetition in resources).
- Endpoint normalization (e.g., ensuring a URL ends with `/api/v1`).
- Template rendering.

```hcl
locals {
  endpoint = endswith(var.coolify_endpoint, "/api/v1")
    ? var.coolify_endpoint
    : "${trimsuffix(var.coolify_endpoint, "/")}/api/v1"
}
```

---

## Local Asset Blocks (no remote provider)

Blocks that write files to the project directory (`dockerfile`, `gitignore`, `dockerignore`) use only the `local` provider — no `terraform` block with `required_providers` is needed.

```hcl
# Generating a templated Dockerfile
resource "local_file" "dockerfile" {
  content  = templatefile("${path.module}/templates/python-pip-nginx.Dockerfile.tftpl", {
    python_version = var.language_version
    nginx_version  = var.server_version
  })
  filename = "${var.target_folder}/Dockerfile"
}
```

Template files live in `{block_folder}/templates/` and use the `.tftpl` extension.

---

## Shell-Heavy Blocks (`terraform_data` + `local-exec`)

When no Terraform provider exists for an API (e.g., specific Coolify endpoints), use `terraform_data` with `local-exec`:

```hcl
resource "terraform_data" "git_local_repo_setup" {
  triggers_replace = [var.target_folder, var.remote_url]

  provisioner "local-exec" {
    working_dir = var.target_folder
    command     = <<EOT
      git init
      git remote add origin ${var.remote_url}
      git branch -M main
    EOT
  }
}
```

**Rules for `local-exec` scripts:**
- Always start with `set -e` to fail fast on errors.
- Use `curl -sf` (silent, fail on HTTP error).
- Store intermediate state (e.g., a created UUID) in a file in `${path.module}/` so the `destroy` provisioner can clean up.
- Always provide a matching `when = destroy` provisioner.

---

## Outputs

Every value another block might need **must** be declared as an output — even if it seems obvious. Output names must be:
- lowercase, snake_case.
- Descriptive but concise (`image_path`, not `docker_image_registry_path`).
- Consistent across providers that serve the same role:

| Role            | Standard output names                             |
|-----------------|---------------------------------------------------|
| Image registry  | `host`, `user`, `token`, `image_path`             |
| Source control  | `clone_url`, `repo_name`                          |
| Compute         | `ip_address`, `public_dns`, `ssh_user`            |
| Deploy target   | `app_uuid`, `app_url`, `webhook_url`              |
| Platform group  | `project_uuid`, `project_name`                    |

Sensitive outputs must be marked accordingly:
```hcl
output "token" {
  value     = gitlab_project_access_token.registry_token.token
  sensitive = true
}
```

---

## Provider Configuration

Provider config goes directly in `main.tf` using variables — never hard-coded credentials, never environment variables (those are the caller's concern). This keeps the block self-contained:

```hcl
provider "gitlab" {
  token = var.gitlab_token
}
```

---

## What NOT to Do

| Anti-pattern                              | Reason                                                 |
|-------------------------------------------|--------------------------------------------------------|
| Using `TF_VAR_*` env vars inside main.tf  | Breaks self-containment; side-channel dependency.      |
| Hard-coding provider endpoints            | Use a variable with a sensible default.                |
| Relying on shared remote state            | Each block manages its own local state via the runner. |
| Putting business logic in `local-exec`    | Keep scripts simple; complex logic belongs in Python.  |
| Using `count` for optional cloud features | Use `count = var.flag ? 1 : 0` only when unavoidable.  |
