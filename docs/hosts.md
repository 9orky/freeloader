# Hosts

Your machines. The Raspberry Pi under the desk, the GPU box in the closet, the VPS you rented six months ago. Freeloader keeps a global inventory of SSH hosts so you can manage and connect to them from anywhere.

Hosts are **not** tied to any project — they're infrastructure that exists before any project and outlives all of them.

## Commands

| Command | What it does |
|---------|-------------|
| `fl hosts scan` | Discover hosts from `~/.ssh/config`, keys, and `known_hosts` |
| `fl hosts import <alias>` | Import a host from SSH config into inventory (or `all`) |
| `fl hosts list` | Show all registered hosts |
| `fl hosts add <alias> <host>` | Register a host manually |
| `fl hosts remove <alias>` | Remove a host from inventory |
| `fl hosts check [alias]` | Check if hosts are reachable (omit alias for all) |
| `fl ssh <alias>` | SSH into a host. That's it. |

## Quickstart

```bash
# What do I already have?
fl hosts scan

# Import everything from SSH config
fl hosts import all

# Or just one
fl hosts import pi

# Add one that's not in SSH config
fl hosts add gpu 10.0.0.5 --user gorky --port 2222 --key ~/.ssh/gpu_key --tags "cuda,home"

# Check connectivity
fl hosts check

# SSH into it
fl ssh pi
```

## Scan

`fl hosts scan` reads your existing SSH setup and gives you a full picture:

```
$ fl hosts scan

🔑 Found 4 SSH key(s) in ~/.ssh/

┌──────────────────────────────────────────────────────┐
│ SSH Config — 3 host(s)                               │
├─────────┬──────────────────┬────────┬────────────────┤
│ Alias   │ Host             │ User   │ Key            │
├─────────┼──────────────────┼────────┼────────────────┤
│ pi      │ 192.168.1.50     │ pi     │ id_ed25519     │
│ gpu     │ 10.0.0.5:2222    │ gorky  │ gpu_key        │
│ old-vps │ 5.78.100.12      │ root   │ id_rsa         │
└─────────┴──────────────────┴────────┴────────────────┘

⚠ Orphan keys (not referenced by any host): hetzner_deploy
⚠ IPs in known_hosts but not in config: 203.0.113.42, 192.168.1.99
```

It cross-references:
- **`~/.ssh/config`** — the full host → IP → user → key mapping
- **`~/.ssh/id_*`** — all private keys, detecting algorithm type
- **`~/.ssh/known_hosts`** — IPs you've actually connected to

Orphan keys and unrecognized known_hosts entries are surfaced so you can clean up.

## Import

After scanning, import hosts into the freeloader inventory:

```bash
# Import one
fl hosts import pi

# Import everything from SSH config
fl hosts import all
```

Imported hosts are stored in `~/.freeloader/hosts.yaml`.

## Manual Add

For hosts not in your SSH config:

```bash
fl hosts add raspberry 192.168.1.50 \
  --user pi \
  --port 22 \
  --key ~/.ssh/id_ed25519 \
  --tags "arm,home,docker"
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--user` | `root` | SSH user |
| `--port` | `22` | SSH port |
| `--key` | `~/.ssh/id_ed25519` | Path to private key |
| `--tags` | — | Comma-separated tags for organization |

## Check

Test connectivity to all hosts or a specific one:

```bash
# Check all
fl hosts check

# Check one
fl hosts check pi
```

Runs a quick `ssh echo ok` with a 5-second timeout. Reports reachable/unreachable with error details.

## SSH Shortcut

The whole point:

```bash
fl ssh pi
```

That's it. Looks up the alias in your inventory, `exec`s into SSH with the right user, key, port, and host. No typing `ssh -i ~/.ssh/id_ed25519 -p 22 pi@192.168.1.50`.

## Storage

The inventory lives at `~/.freeloader/hosts.yaml`:

```yaml
hosts:
- alias: pi
  host: 192.168.1.50
  user: pi
  port: 22
  identity_file: ~/.ssh/id_ed25519
  tags:
  - arm
  - home

- alias: gpu
  host: 10.0.0.5
  user: gorky
  port: 2222
  identity_file: ~/.ssh/gpu_key
  tags:
  - cuda
```

Global, not per-project. Your machines are yours.
