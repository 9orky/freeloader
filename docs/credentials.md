# Credentials

Freeloader keeps all your secrets in an encrypted local vault at `~/.freeloader/secrets.enc`. One passphrase protects everything. No cloud, no SaaS, no `.env` files scattered across repos.

## Commands

| Command | What it does |
|---------|-------------|
| `fl credentials add-provider <name>` | Store provider credentials (github, gitlab, aws, coolify) |
| `fl credentials check <name>` | Verify credentials are valid |
| `fl credentials list-providers` | Show configured providers |
| `fl credentials set <key> <value>` | Store an arbitrary secret |
| `fl credentials get <key>` | Read a secret |
| `fl credentials delete <key>` | Remove a secret |
| `fl credentials list-secrets` | List all stored secret keys |

## Provider Setup

Providers are groups of secrets that a block needs. Instead of setting each key individually, `add-provider` knows what a provider requires and prompts you:

```bash
fl credentials add-provider github
# → prompts for GITHUB_TOKEN
# → validates the token against GitHub API
# → stores encrypted

fl credentials add-provider gitlab
# → prompts for GITLAB_TOKEN

fl credentials add-provider aws
# → prompts for AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

fl credentials add-provider coolify
# → prompts for COOLIFY_TOKEN
```

After adding, credentials are verified automatically. You'll see the authenticated identity (e.g. your GitHub username).

## Arbitrary Secrets

Need to store something that's not a provider token?

```bash
fl credentials set MY_WEBHOOK_URL "https://..."
fl credentials get MY_WEBHOOK_URL
fl credentials delete MY_WEBHOOK_URL
```

## How It Works

- Secrets are encrypted with Fernet (AES-128-CBC) using a key derived from your passphrase via PBKDF2
- The vault file is `~/.freeloader/secrets.enc`
- Every operation that touches secrets prompts for the passphrase
- Nothing leaves your machine
