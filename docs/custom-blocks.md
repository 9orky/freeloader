# Creating Custom Blocks

This is where it gets fun. Freeloader ships with a handful of blocks, but the real power is building your own. A block is just a folder with a `block.yaml` and some files. No Python package to publish. No plugin API to learn.

## Where Blocks Live

Freeloader searches for blocks in two places, in order:

| Location | Purpose |
|----------|---------|
| **Bundled** — `<install-dir>/blocks/_catalog/` | Ships with freeloader. Don't edit these. |
| **User** — `~/.freeloader/blocks/` | Your custom blocks. Overrides bundled ones with the same name. |

If you installed with `pipx` or `uv tool`, the bundled path is somewhere in `~/.local/`. Don't touch it. Put your custom blocks in `~/.freeloader/blocks/` — that's yours.

```
~/.freeloader/
  blocks/
    my-custom-block/
      block.yaml          # ← the contract
      main.tf             # ← for terraform runner
      handler.py          # ← for api runner
      templates/           # ← for generator runner
        something.conf.j2
```

## Anatomy of a Block

Every block needs a `block.yaml`. That's the contract — what runner to use, what it needs, what it gives back.

```yaml
block:
  name: my-custom-block       # unique name, matches the folder
  description: Does something cool
  runner: terraform            # terraform | api | generator
  layer: source                # determines execution order
  provider: github             # optional — groups related secrets
  required_secrets: [MY_TOKEN] # secrets the runner needs at runtime

provides:
  output.key:                  # namespaced output this block produces
    type: string
    description: What this output is

requires:
  input.key:                   # namespaced input from another block
    description: What we need this for
    optional: false            # true = wire only if available

config:
  my_setting:                  # user-facing knob
    type: string               # string | boolean | list
    required: true
    default: some-value
    description: What this controls
    choices: [a, b, c]         # optional — restrict values
```

### Layers

The layer controls execution order. Blocks in earlier layers run first:

```
infra → platform → source → registry → build → deploy → network → data → observe
```

Pick the one that makes sense. Most custom blocks are `build`, `deploy`, or `infra`.

### Provides & Requires — The Wiring System

This is what makes blocks composable. A block **provides** named outputs and **requires** named inputs. Freeloader auto-wires them by matching keys.

```
gitlab-registry provides: registry.image_path
                              ↓ auto-wired
github-actions-ci requires: registry.image_path
```

The naming convention is `namespace.key`. Common namespaces:

| Namespace | Typical keys |
|-----------|-------------|
| `server` | `ip_address`, `instance_id`, `ssh_user`, `public_dns` |
| `source` | `repo_name`, `clone_url` |
| `registry` | `host`, `token`, `user`, `image_path`, `project_id` |
| `platform` | `api_url`, `api_token` |
| `deploy` | `webhook_url`, `app_url`, `app_uuid` |

You can invent your own. As long as one block provides `foo.bar` and another requires `foo.bar`, they'll be wired together.

---

## Writing a Terraform Block

The simplest kind. You write standard Terraform — `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf` — and Freeloader composes them into a workspace.

```
~/.freeloader/blocks/hetzner-vps/
  block.yaml
  main.tf
  variables.tf
  outputs.tf
  versions.tf
```

**Important conventions:**

- **Variables** are auto-injected from `config` and wired `requires`. A config field `server_type` becomes `var.server_type`. A requirement `platform.api_url` becomes `var.platform__api_url` (dots → double underscores).
- **Outputs** must match the `provides` keys. If your block provides `server.ip_address`, your `outputs.tf` must have `output "server__ip_address"`.
- **Secrets** from `required_secrets` are passed as `TF_VAR_<lowercase>` environment variables.

Example `block.yaml`:

```yaml
block:
  name: hetzner-vps
  runner: terraform
  layer: infra
  provider: hcloud
  required_secrets: [HCLOUD_TOKEN]

provides:
  server.ip_address: { type: string }
  server.id: { type: string }

config:
  server_type:
    type: string
    default: cx22
    choices: [cx11, cx22, cx32]
  location:
    type: string
    default: fsn1
```

Example `main.tf`:

```hcl
resource "hcloud_server" "main" {
  name        = var.name
  server_type = var.server_type
  location    = var.location
  image       = "ubuntu-24.04"
}
```

---

## Writing a Generator Block

Generator blocks render Jinja2 templates into the project directory. No state. No API calls. Just files.

```
~/.freeloader/blocks/docker-compose/
  block.yaml
  templates/
    docker-compose.yml.j2
```

**Template conventions:**

- Templates live in a `templates/` subfolder
- File extension `.j2` is stripped: `docker-compose.yml.j2` → `docker-compose.yml`
- Files ending in `.Dockerfile.j2` → `Dockerfile`
- File named `dockerignore.j2` → `.dockerignore`
- `.yml` / `.yaml` files → `.github/workflows/<name>`
- Everything else → project root

**Template context** (available in Jinja2):

| Variable | Content |
|----------|---------|
| `config` | Dict of config values from `freeloader.yaml` |
| `source` | Dict of outputs from source-layer blocks |
| `registry` | Dict of outputs from registry-layer blocks |
| `deploy` | Dict of outputs from deploy-layer blocks |
| *(any namespace)* | Dict of outputs wired via `requires` |

Example template:

```yaml
# docker-compose.yml.j2
version: "3.8"
services:
  app:
    image: {{ registry.image_path }}:latest
    ports:
      - "{{ config.port | default('8080') }}:8080"
    restart: unless-stopped
```

---

## Writing an API Block

API blocks call HTTP endpoints. You write a `handler.py` with three functions:

```
~/.freeloader/blocks/uptime-robot/
  block.yaml
  handler.py
```

`handler.py` must export:

```python
def handle(inputs: dict, config: dict, secrets: dict) -> dict[str, str]:
    """Create or update the resource. Return outputs as {provides_key: value}."""
    ...

def check(inputs: dict, config: dict, secrets: dict) -> bool:
    """Return True if the resource already exists."""
    ...

def destroy(inputs: dict, config: dict, secrets: dict, state: dict) -> None:
    """Tear down the resource. `state` contains previous outputs."""
    ...
```

- `inputs` — resolved values from `requires` (e.g. `{"deploy.webhook_url": "https://..."}`)
- `config` — user config from `freeloader.yaml`
- `secrets` — all secrets the block declared in `required_secrets`
- Return dict keys must match `provides` keys in `block.yaml`

You can use any Python library available in the freeloader environment (`httpx` is already included).

---

## Testing Your Block

```bash
# See if freeloader picks it up
fl blocks list

# Use it in a project — add to freeloader.yaml, then:
fl pipeline plan
```

If the block shows up in `fl blocks list` and the plan resolves without errors, you're good.

---

## Quick Recipe: Cloudflare DNS Block in 5 Minutes

```bash
mkdir -p ~/.freeloader/blocks/cloudflare-dns
cd ~/.freeloader/blocks/cloudflare-dns
```

**block.yaml:**

```yaml
block:
  name: cloudflare-dns
  runner: api
  layer: network
  provider: cloudflare
  required_secrets: [CLOUDFLARE_TOKEN, CLOUDFLARE_ZONE_ID]

provides:
  dns.record_id: { type: string }
  dns.fqdn: { type: string }

requires:
  server.ip_address:
    description: IP to point the DNS record at

config:
  subdomain:
    type: string
    required: true
  proxied:
    type: boolean
    default: true
```

**handler.py:**

```python
import httpx

API = "https://api.cloudflare.com/client/v4"

def _headers(secrets):
    return {"Authorization": f"Bearer {secrets['CLOUDFLARE_TOKEN']}"}

def handle(inputs, config, secrets):
    zone = secrets["CLOUDFLARE_ZONE_ID"]
    resp = httpx.post(
        f"{API}/zones/{zone}/dns_records",
        headers=_headers(secrets),
        json={
            "type": "A",
            "name": config["subdomain"],
            "content": inputs["server.ip_address"],
            "proxied": config.get("proxied", True),
        },
    )
    resp.raise_for_status()
    data = resp.json()["result"]
    return {
        "dns.record_id": data["id"],
        "dns.fqdn": data["name"],
    }

def check(inputs, config, secrets):
    zone = secrets["CLOUDFLARE_ZONE_ID"]
    resp = httpx.get(
        f"{API}/zones/{zone}/dns_records",
        headers=_headers(secrets),
        params={"name": config["subdomain"]},
    )
    return len(resp.json().get("result", [])) > 0

def destroy(inputs, config, secrets, state):
    zone = secrets["CLOUDFLARE_ZONE_ID"]
    record_id = state["dns.record_id"]
    httpx.delete(
        f"{API}/zones/{zone}/dns_records/{record_id}",
        headers=_headers(secrets),
    ).raise_for_status()
```

**Use it:**

```yaml
# freeloader.yaml
blocks:
- use: aws-ec2
  config:
    key_name: my-key
    ssh_public_key: "ssh-ed25519 AAAA..."

- use: cloudflare-dns
  config:
    subdomain: myapp.example.com
```

Freeloader auto-wires `server.ip_address` from `aws-ec2` into `cloudflare-dns`. Done.
