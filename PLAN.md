# Provider And Block Expansion Plan

## Goal

Expand Freeloader with additional free-tier or always-free providers and blocks that fit the existing provider and block contract model.

This plan exists to lock down naming, block contracts, and rollout order before implementation starts.

## Scope

### First wave

- Add `gcp` service provider.
- Add `gcp.vm` block.
- Add `gcp.cloud_run` block.
- Add `gcp.artifact_registry` block.
- Add `vercel` service provider.
- Add `vercel.app` block.
- Add `render` service provider.
- Add `render.service` block.
- Add `render.static_site` block.
- Add `github.pages` block using the existing `github` provider.

### Second wave

- Add `cloudflare` service provider.
- Add `cloudflare.pages` block.
- Add `cloudflare.worker` block.
- Add `neon` service provider.
- Add `neon.postgres` block.
- Add `supabase` service provider.
- Add `supabase.project` block.

## Naming Rules

### Provider names

- Provider folder names remain provider-specific: `gcp`, `vercel`, `render`, `cloudflare`, `neon`, `supabase`.

### Block names

- Use provider-neutral block names when the concept is interchangeable across providers.
- Use provider-specific block names only when the product itself is provider-specific.

### Decisions

- Keep VM blocks named `vm`, not `ec2` or `compute`.
- Use `aws.vm` and `gcp.vm` as the cross-provider VM contract.
- Use provider-native names where they represent a distinct product family, for example `gcp.cloud_run` and `github.pages`.

## Contract Rules

The layer prefix in `requires` and `provides` is the dependency namespace. Interchangeability depends on reusing the same `layer.output_name` keys.

### Existing canonical registry contract

- `registry.host`
- `registry.user`
- `registry.token`
- `registry.image_path`

### New canonical VM contract

Layer: `infra`

- `infra.ip_address`
- `infra.public_dns`
- `infra.ssh_user`
- `infra.instance_id`

`aws.vm` and `gcp.vm` should both provide the same outputs even if their provider-specific implementation details differ.

### New canonical app deploy contract

Layer: `deploy`

- `deploy.app_url`
- `deploy.app_id`

These should be reused by blocks such as `coolify.app`, `vercel.app`, `render.service`, and `gcp.cloud_run` where practical.

### New canonical static site contract

Layer: `deploy`

- `deploy.site_url`
- `deploy.site_id`

These should be used by `github.pages`, `render.static_site`, and `cloudflare.pages`.

### New canonical database contract

Layer: `data`

- `data.host`
- `data.port`
- `data.database`
- `data.user`
- `data.password`
- `data.connection_url`

These should be used by `neon.postgres` and any future managed Postgres block.

## Functional Requirements

### `gcp.vm`

- Must be an ephemeral VM-first block.
- Must generate SSH key material when the user does not provide a key.
- Must inject the public key through instance metadata or cloud-init.
- Must support cloud-init or startup metadata so the machine is reachable from first boot.
- Must expose a consistent SSH user and address output.
- Must default to the always-free-compatible `e2-micro` shape and supported US free-tier regions.
- Must document clearly that GCP free VM eligibility is region-constrained.

### `gcp.cloud_run`

- Must deploy a container image from the canonical registry contract.
- Must return a public service URL.
- Must support simple environment variable input.
- Must default to cost-safe settings that fit hobby or low-traffic use.

### `gcp.artifact_registry`

- Must provide the canonical registry outputs.
- Must create a repository suitable for Docker image push and pull.
- Must align with `github.actions_ci` and any future CI blocks that already consume `registry.*`.

### `vercel.app`

- Must cover static frontend and framework app deployment.
- Must support Git-linked deployment when repository details exist.
- Must support direct project configuration for monorepos.
- Must return the deployed app URL.

### `render.service`

- Must deploy a web service from either repo settings or container image where practical.
- Must return the public service URL.
- Must document the free-tier caveats: spin-down, ephemeral filesystem, and hobby suitability only.

### `render.static_site`

- Must deploy static assets.
- Must return the public site URL.
- Must be positioned as a simpler alternative to `vercel.app` for static-only apps.

### `github.pages`

- Must be a static-site block, not a general Node server block.
- Must support two main modes:
  - plain HTML assets
  - Node-based static build output
- Must generate the workflow or repository configuration needed for Pages publishing.
- Must return the published site URL.

## Service Provider Requirements

### `gcp`

- Auth-based provider.
- Initial credential model uses raw service account JSON stored as a string secret, not a file path.
- Billing support can start as unsupported if direct useful billing integration would slow down delivery.

### `vercel`

- Auth-based provider.
- Requires token-based validation.
- Billing support is optional in the first pass.

### `render`

- Auth-based provider.
- Requires token-based validation.
- Billing support is optional in the first pass.

### Second-wave providers

- `cloudflare`, `neon`, and `supabase` follow the same driver pattern as existing providers.
- First pass can validate credentials and expose provider metadata without implementing billing.

## Delivery Order

### Phase 1: foundation

- Add provider drivers for `gcp`, `vercel`, and `render`.
- Add tests proving provider discovery, naming, and local architecture constraints still pass.
- Add documentation for canonical contracts introduced in this plan.

### Phase 2: GCP path

- Implement `gcp.artifact_registry` first.
- Implement `gcp.cloud_run` second.
- Implement `gcp.vm` third.

This gives Freeloader both image-based and VM-based free-tier deployment paths under one provider.

### Phase 3: hosted app platforms

- Implement `vercel.app`.
- Implement `render.service`.
- Implement `render.static_site`.
- Implement `github.pages`.

### Phase 4: follow-up ecosystem

- Implement `cloudflare.pages` and `cloudflare.worker`.
- Implement `neon.postgres`.
- Implement `supabase.project`.

## Testing Plan

- Add provider tests for each new driver.
- Add block loading tests implicitly through existing block loader coverage.
- Add block resolution tests for any new shared contracts when ambiguity or missing requirements are possible.
- Add focused tests for `github.pages` mode selection.
- Add focused tests for `gcp.vm` defaults and generated SSH behavior where the Python side owns the behavior.

## Validation Plan

- Run `pytest`.
- Run `python -m tests.architecture_rules`.
- Run `ruff check .`.

## Non-Goals For First Pass

- Do not redesign the block resolver.
- Do not add aliasing between `registry.image_url` and `registry.image_path`.
- Do not add a generic schema registry for ports yet.
- Do not try to make every provider support billing before shipping useful blocks.

## Open Questions

- Whether `github.pages` should own workflow generation itself or compose with `github.actions_ci`.
- Whether `vercel.app` and `render.service` should be repo-driven only in v1, or also support direct image deploy in the first implementation.
- Whether `gcp.vm` key generation should be fully Terraform-owned or partially orchestrated by Python before Terraform apply.