# Obtain Token — Architecture Design

## Concept

Before prompting for credentials, run provider-specific guidance steps so users know how to obtain their tokens. Each provider declaratively defines a list of steps. The CLI iterates them sequentially, accumulating a **context dict** that flows from step to step. Steps can collect user input and later steps can interpolate collected values via `{KEY}` placeholders. No framework — just a frozen dataclass, a list, and a dict.

## Approach

Plugin into the existing `ServiceProviderProtocol` — add one property: `obtain_token_steps`.

---

## Changes to `base.py`

```python
@dataclass(frozen=True)
class ObtainTokenStep:
    action: str  # "info" | "open_url" | "input"
    value: str


class ServiceProviderProtocol(Protocol):
    auth_keys: list[str]
    requires_auth: bool
    requires_tech_stack: bool = False
    obtain_token_steps: list[ObtainTokenStep] = []


class ServiceProvider(abc.ABC, ServiceProviderProtocol):
    obtain_token_steps: list[ObtainTokenStep] = []

    @abc.abstractmethod
    def check_credentials(self, credentials: Credentials): ...

    def check_installation(self) -> None: ...
```

New actions are added by extending the `action` literal — no new classes needed.

Supported actions:

| Action      | Behavior                                                                 |
|-------------|--------------------------------------------------------------------------|
| `info`      | Resolve `{KEY}` placeholders from context, print via `console.info`      |
| `open_url`  | Resolve `{KEY}` placeholders from context, print clickable URL           |
| `input`     | Prompt user for value; `value` is the key name (e.g. `COOLIFY_ENDPOINT`); result stored in context under that key |

### Context flow

Steps execute sequentially. A `dict[str, str]` context accumulates across steps:

1. `input` steps **write** to context — `context[step.value] = <user input>`.
2. `info` and `open_url` steps **read** from context — `step.value.format(**context)`.
3. After all steps, context is returned and **merged into credentials**, so `auth_keys` already collected via `input` are not re-prompted.

---

## Provider Examples

### coolify/provider.py

```python
@providers.register("coolify")
class Coolify(ServiceProvider):
    auth_keys = ["COOLIFY_TOKEN", "COOLIFY_ENDPOINT"]
    requires_auth = True
    obtain_token_steps = [
        ObtainTokenStep("input", "COOLIFY_ENDPOINT"),
        ObtainTokenStep("info", "Generate an API token from your Coolify dashboard."),
        ObtainTokenStep("open_url", "{COOLIFY_ENDPOINT}/settings/api-tokens"),
    ]
    ...
```

Flow: prompt for endpoint → show info → show URL with endpoint interpolated → prompt only for `COOLIFY_TOKEN` (endpoint already collected).

### aws/provider.py

```python
@providers.register("aws")
class AWS(ServiceProvider):
    auth_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    requires_auth = True
    obtain_token_steps = [
        ObtainTokenStep("open_url", "https://console.aws.amazon.com/iam/home#/security_credentials"),
    ]
    ...
```

Flow: show URL → prompt for both keys (no inputs collected, nothing to skip).

### github/provider.py

```python
@providers.register("github")
class GitHub(ServiceProvider):
    auth_keys = ["GITHUB_TOKEN"]
    requires_auth = True
    obtain_token_steps = [
        ObtainTokenStep("info", "Create a Personal Access Token with repo scope."),
        ObtainTokenStep("open_url", "https://github.com/settings/tokens/new"),
    ]
    ...
```

### gitlab/provider.py

```python
@providers.register("gitlab")
class GitLab(ServiceProvider):
    auth_keys = ["GITLAB_TOKEN"]
    requires_auth = True
    obtain_token_steps = [
        ObtainTokenStep("info", "Create a Personal Access Token with api scope."),
        ObtainTokenStep("open_url", "https://gitlab.com/-/user_settings/personal_access_tokens"),
    ]
    ...
```

Providers without auth (docker, git) keep the default empty list — no steps shown.

---

## Facade — `facade.py`

Expose steps alongside existing provider data:

```python
def get(self, name: str) -> dict[str, str | bool | list[str] | list[ObtainTokenStep]]:
    provider = load_provider(name)
    return {
        "name": name,
        "requires_auth": provider.requires_auth,
        "requires_tech_stack": provider.requires_tech_stack,
        "auth_keys": provider.auth_keys,
        "obtain_token_steps": provider.obtain_token_steps,
    }
```

---

## Auth Feature — `auth/usecases/_model.py`

```python
@dataclass
class ObtainTokenStepInfo:
    action: str
    value: str


@dataclass
class ProviderInfo:
    name: str
    requires_auth: bool
    requires_tech_stack: bool
    auth_keys: list[str]
    obtain_token_steps: list[ObtainTokenStepInfo]
```

## Auth Feature — `auth/usecases/get_provider.py`

Map `ObtainTokenStep` → `ObtainTokenStepInfo` in the usecase:

```python
def get_provider(name: str) -> ProviderInfo:
    provider = service_providers.get(name)
    return ProviderInfo(
        name=str(provider["name"]),
        requires_auth=bool(provider["requires_auth"]),
        requires_tech_stack=bool(provider["requires_tech_stack"]),
        auth_keys=list(provider["auth_keys"]),
        obtain_token_steps=[
            ObtainTokenStepInfo(action=s.action, value=s.value)
            for s in provider["obtain_token_steps"]
        ],
    )
```

---

## CLI — `auth/ports/cli.py`

Run steps, collect context, merge into credentials, skip already-collected keys:

```python
def _run_obtain_steps(steps: list) -> dict[str, str]:
    context: dict[str, str] = {}
    for step in steps:
        match step.action:
            case "input":
                context[step.value] = typer.prompt(step.value)
            case "info":
                console.info(step.value.format(**context))
            case "open_url":
                console.info(f"→ {step.value.format(**context)}")
    return context


@auth_group.command()
@click.argument("name", required=True)
@console.handle_cli_error
def provider(name: str):
    provider = usecases.get_provider(name)

    collected: dict[str, str] = {}
    if provider.obtain_token_steps:
        collected = _run_obtain_steps(provider.obtain_token_steps)

    remaining_keys = [k for k in provider.auth_keys if k not in collected]
    credentials = {**collected, **console.prompter(remaining_keys, True)}

    usecases.auth_provider(name, credentials)
```

### Coolify example session

```
$ fl auth provider coolify
COOLIFY_ENDPOINT: https://coolify.example.com     ← input step
Generate an API token from your Coolify dashboard. ← info step (resolved)
→ https://coolify.example.com/settings/api-tokens  ← open_url step (resolved)
COOLIFY_TOKEN: ****                                ← only remaining auth_key prompted
✓ Provider coolify authorized.
```

---

## Summary

| What changes            | Where                                 |
|-------------------------|---------------------------------------|
| `ObtainTokenStep` added | `service_providers/base.py`           |
| Protocol gains property | `service_providers/base.py`           |
| Steps declared          | Each `provider.py` with `requires_auth = True` |
| Facade exposes steps    | `service_providers/facade.py`         |
| Model gains field       | `auth/usecases/_model.py`             |
| Usecase maps steps      | `auth/usecases/get_provider.py`       |
| CLI runs steps + merges | `auth/ports/cli.py`                   |

No new packages. No new abstractions. Extend by adding new `action` values and a `case` branch.
