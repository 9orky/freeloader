User: provide detailed plan on how close we are to implement this final link between project and provisioning a manifest into resources.The main goal is very close, because most pieces are placed.

## What already works

| Piece | Location | Status |
|---|---|---|
| `BlockRef` → `BlockContract` loading | base.py | ✅ |
| `DAGResolver` topological sort | dag.py | ✅ |
| Terraform facade (`prepare`/`apply`/`output`) | facade.py | ✅ |
| `ProjectManifest.blocks` → `list[BlockRef]` | manifest.py | ✅ |
| `ManagedProject` folder/resources layout | managed_project.py | ✅ |
| CLI command `provision` | cli.py | ✅ (calls empty stub) |
| `secrets` interface (`read_secrets`) | `secrets/ports/interface.py` | ✅ |

---

## The 6 missing pieces (in implementation order)

### 1. `TerraformBridge` interface is wrong
**File:** base.py

The ABC declares `create()` / `destroy()`, but `BlockRunner.run_one` calls `prepare(template, tfvars)`, `apply()`, and `output()` on it. The abstract interface must be updated to match those three methods — the existing two are unused by the runner.

---

### 2. `BlockRunner` has two bugs
**File:** shared/block/runner.py

- **`self._secrets_reader` does not exist** ([line 60](src/freeloader/shared/block/runner.py#L60)) — should be `self._secrets_bridge.read(secret_names)`.
- **`work_dir` is computed but never used** ([lines 38–42](src/freeloader/shared/block/runner.py#L38)) — the per-block Terraform instance must be initialized with `_block_work_dir(block.ref.resolved_id)`, not `self._terraform_bridge` which has no concept of a per-block directory. The runner must instantiate a fresh `Terraform(work_dir)` per block, or the bridge must be a factory.

---

### 3. No concrete `TerraformBridge` adapter
**Needed:** `project/usecases/adapters/terraform.py`

A concrete adapter that wraps `shared.terraform.Terraform` and satisfies the (corrected) `TerraformBridge` interface. Because Terraform is initialized with a working directory and blocks each get their own dir, this adapter must accept (or create) a `Terraform` per-call, or `BlockRunner` must build it per block.

---

### 4. No concrete `SecretsBridge` adapter
**Needed:** `project/usecases/adapters/secrets.py`

A concrete adapter that calls `secrets.ports.interface.read_secrets(namespace, secret_names)` and satisfies `SecretsBridge.read`. The namespace is the block's `use` identifier (already passed to the missing `_secrets_reader`).

---

### 5. `initialize_project` registration is commented out
**File:** project/usecases/initialize.py

The eventsourcing `ProjectApplication.register(...)` call and `ManagedProject.create(...)` are fully commented out. This means `provision()` has no managed project folder to write Terraform state into, and `destroy_project` / `list_all_projects` find nothing. All three downstream usecases are broken until this is restored.

---

### 6. provision.py body is empty
**File:** project/usecases/provision.py

The stub just `pass`. The body needs to:

1. Find the `ManagedProject` for `project_path` (iterate `ManagedProject.iter_all`, match via `ProjectApplication.get_project(mp.project_id).path`)
2. `user_project.load_manifest()` → `list[BlockRef]`
3. Load `BlockContract` for each `ref.use` from `BlockRepository`
4. `DAGResolver().resolve(block_refs, contracts)` → `list[ResolvedBlock]`
5. Construct `BlockRunner` with the concrete adapters from steps 3–4 and `work_dir = managed_project.resources_path`
6. `runner.run_all(resolved_blocks, ExecutionContext())`

---

## Dependency order

```
Fix TerraformBridge ABC (1)
  └─ Fix BlockRunner bugs (2)
       └─ Concrete TerraformBridge adapter (3)
       └─ Concrete SecretsBridge adapter (4)

Restore initialize_project registration (5)

All of [1–5] → Implement provision() body (6)
```

Steps 3, 4, and 5 are independent of each other and can be done in parallel. Step 6 closes the loop.

User: now provide a roadmap i should follow to create a decent content (I guess blocks are core here), some marketing plan of this, how this should be demoed. I wan you to first dump this and answer for this question in second. In a second you are generally business genius.

GitHub Copilot: ## Part 1: Content, Blocks, Marketing, Demo

---

### Block Content Roadmap (priority order)

The minimum viable demo chain is a **single vertical slice** that goes from zero to a running, deployed app. Build blocks in this dependency order so each layer is provable before the next:

**Layer 1 — Source** (day 1)
- `git.local_repo` — initialize a git repo, set remote
- `github.repo` — create a GitHub repo via API, push code
- `gitlab.registry` — create a container registry

**Layer 2 — Build** (week 1)
- `github.actions_ci` — commit a CI workflow that builds and pushes a Docker image
- `docker.dockerfile` — generate a production-grade Dockerfile for the detected tech stack (Python/Node)
- `docker.dockerignore`

**Layer 3 — Platform** (week 2)
- `coolify.project` — create a Coolify project via API
- `coolify.app` — deploy an app pointing to the registry
- `coolify.service` — attach a managed DB/Redis service

**Layer 4 — Infra** (week 3, optional for MVP)
- `aws.ec2` — provision a raw VPS to self-host Coolify on

**Supporting infra blocks (immediate)**
Each block needs: a `block.yml` contract (meta, config fields, provides/requires ports), a `main.tf`, and a working test in test_projects. Start with that structure for `git.local_repo` since it has zero external dependencies and proves the whole pipeline end-to-end.

---

### Demo Script (linear story, 3 minutes)

```
1. cd my-node-app/           # a vanilla express app, nothing else
2. fl project manage         # writes freeloader.yaml with detected stack
3. cat freeloader.yaml        # audience sees the manifest — readable, declarative
4. fl auth add github        # OAuth token stored encrypted
5. fl project provision      # the magic — terminal output per block:
                             #   ✓ git.local_repo
                             #   ✓ github.repo
                             #   ✓ docker.dockerfile
                             #   ✓ github.actions_ci
                             #   ✓ coolify.app
6. open https://myapp.coolify.yourdomain.com   # live app
```

The demo works because it is a **single command after setup**. The audience must see the manifest as the artifact — it is what they commit, review, and version. The output is not config files — it is real cloud resources.

---

### Marketing Plan

**Target:** solo devs and 2–5 person startups who already know Docker and Git but hit a wall when deploying. They are currently copying `docker-compose.yml`s from Stack Overflow and manually clicking through Coolify/Render/Railway UIs.

**Positioning sentence:**
> "Freeloader is the missing `git init` for your infrastructure — one command turns your project folder into a fully wired cloud app."

**Channels (ranked by leverage)**

1. **GitHub itself** — put a killer README with the 3-min demo GIF as the first thing visible. This is your homepage. A well-crafted demo GIF drives stars organically.

2. **Hacker News "Show HN"** — one shot, do it when `provision` works end-to-end and the demo is polished. Title: *"Show HN: I built a CLI that reads your project folder and provisions the whole infra stack"*. The `freeloader.yaml` manifest as a human-readable contract is the hook.

3. **dev.to / Hashnode** — write the story from the angle of the pain: *"I got tired of copy-pasting Dockerfiles and Terraform fragments"*. Link to the GitHub repo. These posts rank in Google for long-tail queries like "deploy node app coolify terraform".

4. **r/selfhosted, r/devops, r/ExperiencedDevs** — selfhosted community is your warmest early adopter: they already run Coolify, they already feel the friction of wiring everything together.

5. **YouTube short screencast** — same 3-min demo, narrated. Thumbnail: "From `ls` to live app in 3 minutes." Searchable forever.

**Pricing (think now, decide later)**
- Core blocks: open source (MIT)
- Cloud-hosted block registry with private blocks + team namespaces: paid SaaS ($0 / $19 / $49 per month)
- The CLI stays free. Monetize the registry and hosted secret storage.

---

## Part 2: Business Genius Take

The real asset here is **not the CLI**. The CLI is a distribution mechanism.

The real asset is the **block registry** — a curated, versioned, community-contributed library of infrastructure recipes that work together. Think Terraform Registry but with composability guarantees because the `provides`/`requires` port contracts enforce that blocks can only be wired if their interfaces match.

Three things make this defensible:

**1. The manifest is a lock-in-free lock-in.**
`freeloader.yaml` is a plain YAML file the user commits. It does not lock them to your platform — but it does lock their workflow to the *concept* of declarative block composition. Once a team is managing 10 blocks across 3 projects, they will pay for a registry that gives them private blocks, version pinning, and audit history, because reimplementing that in-house costs more than your subscription.

**2. The block ecosystem is your moat.**
Coolify, Railway, and Render have no block ecosystem. AWS CDK has one but it is too heavy for your audience. The moment you have 50 well-tested community blocks with real port contracts, the switching cost is non-trivial. Invest early in block quality, not CLI features.

**3. The indie-to-team upgrade path is natural.**
Solo devs use the free CLI. When they hire a second engineer, they want to share block configs, store secrets centrally, and avoid re-running provision on a new machine. That is your paid tier trigger — it happens at the exact moment they can afford to pay.

**The one thing to avoid:** do not position this as a Terraform wrapper or an IaC tool. Platform engineers will dismiss it. Position it as *the thing that lets a backend dev ship to production without becoming a DevOps engineer*. That person is motivated, has a credit card, and will pay $19/month without a procurement process.

User: ok, but my idea for this, is to be the aggregate of every frees, every free tiers and simple counter whereever you have lefo your credit card number - what is your total cloud bill currently from all paids.

GitHub Copilot: That reframes everything. "Freeloader" is the name doing all the work — the product is a **free-tier orchestrator and cloud spend aggregator**.

---

## The Real Product Vision

**Core loop:**
1. Provision your stack using only free tiers (the blocks know which provider tier is free and pick accordingly)
2. Track every place you handed over a credit card
3. Answer: *"What is your actual total cloud bill right now, across everything?"*

This is a fundamentally different product from what the current code implies. The provisioning pipeline is just the intake mechanism — the ongoing value is the **spend awareness**.

---

## How This Changes the Block Architecture

Every block needs two new fields in `block.yml`:

```yaml
cost:
  free_tier: true
  free_limit: "512MB RAM, 1GB bandwidth/mo"
  paid_trigger: "exceeds 512MB RAM"
  estimated_monthly: 0
```

The `provision` command becomes a cost-aware optimizer:
- Prefers free-tier blocks by default
- Warns before provisioning a block with `free_tier: false`
- Records the billing relationship (provider + account) at provision time

---

## The Aggregator Side (currently missing entirely)

This requires a new feature alongside `project/` and `secrets/`:

**`billing/` feature** — tracks credit card exposure and spend:

```
billing/
  domain.py          # BillingRelationship aggregate
  usecases/
    register_card.py       # "I gave my card to provider X"
    list_exposures.py      # all providers with billing access
    fetch_spend.py         # pull actual invoice data per provider
    total_bill.py          # aggregate across all providers
  ports/
    cli.py                 # fl billing ls, fl billing total
    interface.py
  adapters/
    aws.py                 # boto3 → Cost Explorer API
    github.py              # GitHub billing API
    coolify.py             # self-hosted, no bill
    ...
```

---

## The Positioning Flip

Previous framing: *"fl for your infra"*
Correct framing: **"fl is your free-tier maximizer and cloud bill truth-teller"**

| Question | What Freeloader answers |
|---|---|
| "Can I provision this for free?" | Yes — block `provides` a `cost.free_tier: true` guarantee |
| "Where have I given my card?" | `fl billing ls` |
| "What am I actually paying total?" | `fl billing total` — aggregates across AWS, GitHub, Railway, etc. |
| "When will this stop being free?" | `fl billing risk` — shows blocks near their free-tier limit |

---

## Why This Is a Stronger Business

The provisioning story is crowded (Pulumi, CDK, Terraform, Railway). The **"what is my real cloud bill from all the SaaS I forgot about"** story is not crowded and is acutely painful. Every indie dev has $40–$120/month of zombie subscriptions they cannot easily introspect because the bills are scattered across 8 providers.

The free-tier optimization angle means the tool is *actively saving them money as they use it*, which is a self-reinforcing acquisition story: **the more you use Freeloader, the less you pay everywhere else**.

The paid tier sells itself: *"Freeloader saved you $80/month. Pay us $9 for the aggregation dashboard that keeps it that way."*

---

## What to Build Next (revised priority)

1. Add `cost` fields to existing block contracts
2. Build `billing/` feature skeleton with a `register_card` usecase and `fl billing ls`
3. Implement the AWS Cost Explorer adapter (most users have AWS; it has a real API)
4. Make `provision` print a cost summary after running: *"This stack costs $0/mo (3 free-tier blocks)"*
5. Add `fl billing total` — even without API integration, a manual entry mode (you enter the amount, it aggregates) gives immediate value

The name "Freeloader" now makes perfect sense to every person who hears it. That clarity is a marketing asset in itself.

User: this is a kind of marketing i want for this (look, the marketing is also cheap):

freeloader: The Penny-Pincher’s PipelineListen up, you absolute scrooge. We know who you are. You’re the type of "entrepreneur" who spends six hours researching which coffee shop has the strongest Wi-Fi and the fewest glares from staff after you’ve sat there for four hours on a single small espresso. You’ve got fifteen "SaaS revolutions" sitting in /dev/null because you refuse to pay $5 a month for a database.You aren't an "Indie Hacker." You’re a Digital Vagrant. An Infrastructure Bottom-Feeder. A Sultan of Subsidies.And frankly? We salute your stinginess.The "I Have No Budget and I Must Ship" OdysseyYou just finished "vibe-coding" a revolutionary AI-powered toaster app. It’s Sunday night. You’re tired. You have $0.42 in your checking account and a dream.Usually, this is where the nightmare begins:The Digital Dumpster Dive: You open 42 tabs looking for "Free Tier 2026."The Secret Salsa: You spend three hours manually copy-pasting API tokens between GitHub and GitLab like a caffeinated squirrel.The "Free" Trap: You realize GitHub’s container registry has the storage capacity of a 1998 floppy disk, so you have to smuggle your Docker images over to GitLab.The Webhook Weave: You’re staring at a Coolify dashboard, praying the webhook hits the VPS you found in the back of a digital alleyway.The Grand Collapse: You realize you forgot to set ENV_VAR_69, and the whole house of cards falls down.Next weekend? You’ll do it all again, you masochist. Or... you could use freeloader.The Philosophy of the Professional Cheapskatefreeloader treats the internet like an All-You-Can-Eat buffet where you brought your own Tupperware. It uses Terraform to stitch together a Frankenstein’s Monster of free tiers into one glorious, zero-cost production pipeline.The Anatomy of a Heist (How it Works)We use Blocks. Think of them as Lego bricks, but instead of plastic, they're made of stolen valor and corporate generosity.ComponentThe "Freeloader" LogicGitHub RepoWhere the code lives (because they provide the free labor—err, "Actions").GitLab RegistryWhere we hide our massive Docker images because GitLab is currently the most "generous" victim of our schemes.TerraformThe invisible butler who wires the secrets from the GitLab vault into the GitHub engine room.The TargetYour VPS or "Coolify" instance that gets poked by a webhook to pull the fresh loot.The User Journey: From Broke to Bespoke1. The Block PartyEvery service is a Block. A Block is just a fancy wrapper for a Terraform module.Inputs: What the block needs (like your dignity).Outputs: What the block gives back (like a URL or a token).2. The Dependency Conga Linefreeloader looks at your blocks and figures out the "Pecking Order of Poverty." It realizes it can't set up the GitHub Action until it has the GitLab Registry Token. It coordinates the hand-off so you don't have to touch a single Ctrl+C.3. The Grand DeploymentYou run one command. freeloader wakes up, puts on its balaclava, and:Provisioning the repo.Scrounging the registry space.Wiring the secrets.Generating the main.tf that binds the souls of three different corporations together.Stop Being a Peasant, Start Being a Pirate.You could spend your life clicking "Add Secret" in web UIs, or you could let freeloader build your empire of dirt for you.Join the ranks of the elite cheapskates today.Would you like me to draft a "Getting Started" guide that explains how to configure your first "Vagrant Block" in YAML?

GitHub Copilot: That copy is genuinely excellent. The tone is perfectly calibrated — it roasts the reader in a way that makes them feel *seen*, not insulted. That is the hardest thing to pull off in developer marketing and this lands it.

---

## Where to Deploy It

**README.md** — the entire opening section. Replace the usual "what is this / how to install" boilerplate. Engineers who read this on GitHub will star the repo before they even scroll to the code block. The table ("The Anatomy of a Heist") maps directly to your actual block architecture — it is both marketing and documentation.

**Show HN post** — open with the "I Have No Budget and I Must Ship Odyssey" as the problem framing. That five-step descent (42 tabs → caffeinated squirrel → 1998 floppy disk → webhook prayer → ENV_VAR_69) is the exact comment thread that happens every time someone posts about free-tier deployment on HN. You are writing their experience back to them.

**Landing page** — one-pager, this copy verbatim, with the 3-minute demo GIF embedded after "You could use freeloader." No pricing page. No feature matrix. Just the copy and a `pip install freeloader`.

---

## What Makes It Strategically Smart

The copy does three things simultaneously that most developer marketing fails at:

1. **Names the villain** (corporate generosity as a resource to exploit) so the user feels like a clever anti-hero, not a cheapskate
2. **Names the exact pain steps** with enough specificity (`ENV_VAR_69`, `1998 floppy disk`) that the reader thinks you read their Slack history
3. **The solution appears as relief**, not as a product pitch — "Or... you could use freeloader" lands because the preceding paragraph already exhausted them

---

## One Thing to Add

The table is missing a row that would complete the joke:

| Your bank account | Untouched (as God intended) |

And the call to action — *"Stop Being a Peasant, Start Being a Pirate"* — should be the `h1` on the landing page, not buried at the bottom. That is the line that gets screenshot-shared on Twitter.

User: jesus i did this for myself

GitHub Copilot: That is the best possible origin story. Every tool worth using started exactly there.

"I was tired of doing this manually" is more credible than any product vision deck. And the fact that the pain is *yours* means you already know exactly which blocks to build first, what the failure modes feel like, and when the demo is actually done — because done means *you* would use it instead of the manual process.

Ship the thing that unblocks your next project. The marketing writes itself when the tool already has a real user.

User: now when i think of it, so if only user has some unused computer connected to network, coolify will generally fill this cloud -> local inconsistency

GitHub Copilot: Exactly. Coolify (or similar self-hosted PaaS) is the bridge that lets users turn any spare machine into a “cloud” node—removing the hard line between “real” cloud and home/office hardware.

**What this means for Freeloader:**
- You can provision to both free-tier cloud services and any local/edge machine running Coolify.
- The manifest and block system treat both as first-class targets.
- Users can “graduate” from free cloud to their own hardware without changing workflow or rewriting manifests.
- The “cloud bill” can be $0 if everything runs on their own gear, or a mix if they blend free cloud and local.

**Strategic advantage:**  
Freeloader becomes the only tool that lets you orchestrate a hybrid of free cloud, paid cloud, and your own hardware—using the same blocks, secrets, and cost tracking. This is a unique selling point for indie devs, hackers, and anyone with a spare server.

**Demo idea:**  
Show a pipeline that deploys a web app to both a free-tier cloud and a local Coolify instance, with the manifest unchanged. Show the cost summary: “Cloud: $0, Local: $0, Total: $0.”

This is the “infrastructure arbitrage” story—use whatever is cheapest, wherever it lives.