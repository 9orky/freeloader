# Costs Module — Architecture Design

## Overview

Costs awareness across two axes:

1. **Static** — block-level cost metadata declared in `block.yml` (tier, free-tier limits, estimates).
2. **Dynamic** — provider-level billing fetched via API (current spend, free-tier usage).

Billing is strictly separated from auth. Each supporting provider gets its own `billing.py` next to `provider.py`. A single `costs.py` in `service_providers/` orchestrates lookups.

---

## Package Tree

```
service_providers/
  base.py              # ServiceProvider ABC (unchanged)
  costs.py             # BillingAdapter ABC, BillingCheckCost, BillingReport models,
                       #   orchestrator: supports_billing(), get_billing_check_cost(), fetch_billing()
  registry.py          # unchanged
  facade.py            # unchanged
  obtain.py            # unchanged
  aws/
    provider.py        # ServiceProvider (auth only — unchanged)
    billing.py         # AWSBilling(BillingAdapter)
  github/
    provider.py        # unchanged
    billing.py         # GitHubBilling(BillingAdapter)
  gitlab/
    provider.py        # unchanged
    billing.py         # GitLabBilling(BillingAdapter)
  coolify/
    provider.py        # unchanged (no billing.py — self-hosted)
  docker/
    provider.py        # unchanged (no billing.py — local tool)
  git/
    provider.py        # unchanged (no billing.py — local tool)
```

Changed modules:

| Module | Change |
|---|---|
| `block/contract.py` | Add `BlockCostSpec` model, add `costs` field to `BlockContract` |
| `service_providers/costs.py` | New — `BillingAdapter` ABC, billing models, orchestrator functions |
| `service_providers/aws/billing.py` | New — `AWSBilling(BillingAdapter)` |
| `service_providers/github/billing.py` | New — `GitHubBilling(BillingAdapter)` |
| `service_providers/gitlab/billing.py` | New — `GitLabBilling(BillingAdapter)` |

---

## Block Contract Extension

### `block.yml` schema addition

```yaml
costs:
  tier: always_free | free_tier | paid
  free_tier_limits:
    - metric: compute_hours
      amount: 750
      period: monthly
  estimated_monthly_usd: "0.00"
  note: "Free for 12 months after AWS account creation"
```

All fields optional except `tier`. Blocks without a `costs` key default to `tier: paid` (safe default — forces explicit opt-in to free).

### Examples per existing block

| Block | Tier | Note |
|---|---|---|
| `git.gitignore` | `always_free` | Local tool |
| `git.local_repo` | `always_free` | Local tool |
| `docker.dockerfile` | `always_free` | Local file generation |
| `docker.dockerignore` | `always_free` | Local file generation |
| `github.remote_repo` | `free_tier` | Free for public repos, limits on private |
| `github.actions_ci` | `free_tier` | 2000 min/month on free plan |
| `gitlab.registry` | `free_tier` | 5 GB registry storage on free plan |
| `aws.ec2` | `free_tier` | 750 hrs/month t2/t3.micro for 12 months |
| `coolify.project` | `always_free` | Self-hosted, no provider charge |
| `coolify.app` | `always_free` | Self-hosted |
| `coolify.service` | `always_free` | Self-hosted |

---

## `block/contract.py` — Cost Spec (static metadata)

```python
class CostTier(str, Enum):
    always_free = "always_free"
    free_tier = "free_tier"
    paid = "paid"


class FreeTierLimit(BaseModel):
    metric: str
    amount: float
    period: str


class BlockCostSpec(BaseModel):
    tier: CostTier = CostTier.paid
    free_tier_limits: list[FreeTierLimit] = []
    estimated_monthly_usd: str = ""
    note: str = ""


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: list[ConfigField] = []
    costs: BlockCostSpec = BlockCostSpec()
```

Block-level cost types live in `block/contract.py` (upstream of `service_providers`). No circular dependency — `costs.py` never imports from `block/`.

---

## `service_providers/costs.py` — Billing (dynamic data)

Single flat module. Owns all billing-specific types and the `BillingAdapter` ABC. Completely independent of `base.py` / `ServiceProvider` — billing never touches auth.

### Models

```python
from enum import Enum
from abc import ABC, abstractmethod
from pydantic import BaseModel

from .base import Credentials


class BillingCheckCost(str, Enum):
    free = "free"
    paid = "paid"


class BillingLineItem(BaseModel):
    service: str
    amount_usd: float
    currency: str = "USD"


class FreeTierUsage(BaseModel):
    service: str
    metric: str
    used: float
    limit: float
    unit: str


class BillingReport(BaseModel):
    provider: str
    total_usd: float
    currency: str = "USD"
    period: str
    items: list[BillingLineItem] = []
    free_tier_usage: list[FreeTierUsage] = []
```

### `BillingAdapter` ABC

```python
class BillingAdapter(ABC):
    billing_check_cost: BillingCheckCost

    @abstractmethod
    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...
```

Completely separate from `ServiceProvider`. A provider that supports billing has a `billing.py` with a class extending `BillingAdapter` — it never subclasses or mixes into `ServiceProvider`.

### Billing registry + orchestrator functions

```python
billing_adapters = LazyRegistry[BillingAdapter]("BillingAdapterRegistry")


def supports_billing(provider_name: str) -> bool: ...

def get_billing_check_cost(provider_name: str) -> BillingCheckCost: ...

def fetch_billing(provider_name: str, credentials: Credentials) -> BillingReport: ...
```

Each provider's `billing.py` registers itself via `@billing_adapters.register("aws")`, mirroring how `provider.py` uses `@providers.register("aws")`.

---

## Provider billing support matrix

| Provider | Has `billing.py` | `billing_check_cost` | API |
|---|---|---|---|
| `aws` | Yes | `paid` | Cost Explorer ($0.01/request) |
| `github` | Yes | `free` | Billing API |
| `gitlab` | Yes | `free` | Namespace storage / usage API |
| `coolify` | No | — | Self-hosted, no billing concept |
| `docker` | No | — | Local tool |
| `git` | No | — | Local tool |
| `gcp` | Yes (future) | `free` | Cloud Billing API |
| `hetzner` | Yes (future) | `free` | Billing API |
| `vercel` | Yes (future) | `free` | Usage API |

---

## Per-Provider `billing.py` Signatures

### `aws/billing.py`

```python
from ..costs import BillingAdapter, BillingCheckCost, BillingReport, billing_adapters
from ..base import Credentials


@billing_adapters.register("aws")
class AWSBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.paid

    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...
```

Uses `boto3` Cost Explorer `get_cost_and_usage` for current month spend. Returns `BillingReport` with line items per service and free-tier usage where available.

### `github/billing.py`

```python
from ..costs import BillingAdapter, BillingCheckCost, BillingReport, billing_adapters
from ..base import Credentials


@billing_adapters.register("github")
class GitHubBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.free

    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...
```

Uses `PyGithub` billing endpoints for Actions minutes and storage usage.

### `gitlab/billing.py`

```python
from ..costs import BillingAdapter, BillingCheckCost, BillingReport, billing_adapters
from ..base import Credentials


@billing_adapters.register("gitlab")
class GitLabBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.free

    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...
```

Uses `python-gitlab` namespace usage and storage quota APIs.

---

## Dependency Direction

```
block/contract.py  ←  defines CostTier, FreeTierLimit, BlockCostSpec (static block metadata)

service_providers/costs.py  ←  defines BillingAdapter ABC, BillingCheckCost,
                                BillingReport, BillingLineItem, FreeTierUsage
                                + billing_adapters registry + orchestrator functions
                                imports only: base.Credentials
      ↑
service_providers/{provider}/billing.py  ←  implements BillingAdapter
                                            imports only: costs.py, base.Credentials
```

No cross-dependency between `billing.py` and `provider.py`. They share the provider directory but import from different parents (`costs.py` vs `base.py`). Auth and billing are fully decoupled.

---

## CLI Integration

Costs surfaces in two places:

### 1. Block provisioning — automatic cost display

During `fl project provision` or block selection, always show cost tier and free-tier limits for each selected block. No API call needed — static metadata from `block.yml`.

### 2. Provider billing check — explicit command

```
fl providers billing <provider_name>
```

Flow:
1. Call `supports_billing(provider_name)` — if false, inform user and stop.
2. Call `get_billing_check_cost(provider_name)` — if `paid`, warn user and confirm.
3. Load credentials from secrets store.
4. Call `fetch_billing(provider_name, credentials)` → display `BillingReport`.

---

## Provider Implementation Example — AWS

`aws/provider.py` — auth only, unchanged:

```python
@providers.register("aws")
class AWS(ServiceProvider):
    auth_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    requires_auth = True

    def check_credentials(self, credentials: Credentials) -> None: ...
```

`aws/billing.py` — billing only, separate file:

```python
@billing_adapters.register("aws")
class AWSBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.paid

    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...
```

`fetch_billing` uses `boto3` Cost Explorer `get_cost_and_usage` for current month spend and `get_cost_forecast` for estimates. Returns `BillingReport` with line items per service and free-tier usage where available.
