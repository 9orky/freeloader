# Block Port Contracts

Freeloader resolves block dependencies by matching `requires` keys against `provides` keys in the form `layer.output_name`.

If two blocks are meant to be interchangeable, they must reuse the same contract keys.

## Naming Rule

- Use provider-neutral block names for interchangeable concepts such as `aws.vm` and `gcp.vm`.
- Use provider-specific block names for provider-native products such as `github.pages` and `gcp.cloud_run`.
- Use provider-neutral port names whenever another provider can realistically satisfy the same requirement.

## Canonical Contracts

### Registry

Layer: `registry`

- `registry.host`
- `registry.user`
- `registry.token`
- `registry.image_path`

These outputs are already consumed by blocks such as GitHub Actions and Coolify deployment blocks.

### Virtual Machine

Layer: `infra`

- `infra.ip_address`
- `infra.public_dns`
- `infra.ssh_user`
- `infra.instance_id`

This is the canonical contract for VM-style blocks. Provider implementations may differ, but their outputs should not.

### App Deployment

Layer: `deploy`

- `deploy.app_url`
- `deploy.app_id`

Use this for deploy blocks that publish a runnable web application.

### Static Site Deployment

Layer: `deploy`

- `deploy.site_url`
- `deploy.site_id`

Use this for static-site blocks such as Pages-style hosting.

### Managed Database

Layer: `data`

- `data.host`
- `data.port`
- `data.database`
- `data.user`
- `data.password`
- `data.connection_url`

Use this for managed Postgres-style blocks and similar future database providers.

## Notes

- The `layer` value is part of the dependency namespace, not just display metadata.
- A block that requires `registry.image_path` will only match a selected block that provides `image_path` from the `registry` layer.
- If two selected blocks provide the same `layer.output_name`, resolution is ambiguous and the pipeline fails.