# Pivot Checklist

What to do *this weekend* to move from the Azure version to this OSS version. Designed for someone who finished Week 1, Saturday of the Azure build.

## Decision: archive or replace?

You have two paths. Pick one before you start.

### Path A — Archive the old, start the new (recommended)

Treat the Azure repo as a "previous iteration" you can reference later. Start fresh with this OSS skeleton. Clean break, no confusion about which week you're on.

### Path B — Rebrand the old repo in place

Keep the same GitHub repo, rip out the Azure-specific files, drop in the OSS files. Preserves the commit history. More work, more chances for stale stuff to linger.

Path A is what the rest of this checklist assumes. Path B notes are at the bottom.

---

## Path A: clean restart

### Step 1 — Park the old repo (5 min)

```bash
cd /path/to/project-ouroboros  # the Azure version
git checkout -b azure-archive
git push origin azure-archive
# In GitHub UI: rename the repo to project-ouroboros-azure-archive
# and mark it as archived (Settings → bottom of page)
```

You now have a permanent reference. You can read your old Bicep templates and KQL anytime, but you won't accidentally commit to it.

### Step 2 — Create the new GitHub repo (2 min)

In the GitHub UI:
- Repository name: `project-ouroboros-oss` (or `project-ouroboros` if you want the cleaner name and the archive holds the suffix)
- Public
- Add a README (uncheck — we have our own)
- License: MIT
- `.gitignore`: none (we have our own)

Do **not** initialize it. We're pushing a populated tree.

### Step 3 — Drop the OSS skeleton into a fresh directory (5 min)

```bash
cd ~/work
tar -xzf project-ouroboros-oss-skeleton.tar.gz
cd project-ouroboros-oss
git init
git add .
git commit -m "feat: initial OSS skeleton (pivot from Azure)"
git branch -M main
git remote add origin git@github.com:justinkok28/project-ouroboros-oss.git
git push -u origin main
```

### Step 4 — Wire up GitHub Pages for docs (3 min)

In the new repo's GitHub UI:
- Settings → Pages
- Source: GitHub Actions
- (The included `.github/workflows/docs.yml` will publish on every push to `main`.)

### Step 5 — Configure repo secrets (5 min)

In the new repo's GitHub UI: Settings → Secrets and variables → Actions → New repository secret.

Add:
- `OPENROUTER_API_KEY` — for CI to run integration tests against the live OpenRouter API (optional but useful)

You do *not* need cloud credentials in CI for the OSS version. That's part of the simplification.

### Step 6 — Sign up for Oracle Cloud Always Free (15 min, but with caveats)

Go to [oracle.com/cloud/free](https://www.oracle.com/cloud/free/). Sign up. You will need:
- A working credit card (not charged on free tier, used for identity verification)
- A phone number for SMS verification

**Realistic expectation:** Oracle's free-tier ARM capacity is heavily oversubscribed. Provisioning an Ampere A1 instance frequently fails with "Out of host capacity." Have a fallback: x86 micro tier (1/8 OCPU, 1 GB RAM) is also free, two of them. You can also try Ampere A1 in different regions / different times of day.

If you can't get a free-tier instance after a week of trying, fall back to a $5–6/month Hetzner CAX11 (ARM, 4 GB RAM) — same architecture, no oversubscription, more predictable.

### Step 7 — Sign up for OpenRouter (5 min)

Go to [openrouter.ai](https://openrouter.ai/). Sign up, fund $10. Create an API key. Set a $20/month spend cap in account settings.

Test it locally:

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nousresearch/hermes-3-llama-3.1-70b",
    "messages": [{"role": "user", "content": "Reply with the JSON {\"ok\": true}"}]
  }'
```

### Step 8 — Local dev setup (10 min)

On your laptop:

```bash
# Python 3.11+ with uv (faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Inside the repo:
cp .env.example .env
# fill in OPENROUTER_API_KEY at minimum

# Set up the agent dev environment
cd agent
uv venv
source .venv/bin/activate
uv pip install -r requirements-dev.txt

# Run the test suite — should pass on the skeleton
pytest
```

### Step 9 — Verify CI is green on the empty skeleton

Push a tiny change (e.g., update README), watch the CI workflow on GitHub. The included `ci.yml` runs lint + tests; both should pass on the skeleton because the tests are placeholder. Once CI is green, you've validated the pipeline.

### Step 10 — Read the week-2 playbook and stop

`docs/weeks/week-02-oracle-vm.md` is your next task. Don't skim ahead. Sunday is for setting up the Oracle VM, installing Docker, and running `make up` on the VM for the first time.

---

## Path B: rebrand in place

If you want to keep the existing repo and its history:

1. `git checkout -b azure-snapshot && git push origin azure-snapshot` — preserve a branch reference.
2. `git checkout main`
3. Delete the Azure-specific directories: `git rm -r infra/bicep/ detections/kql/ automation/logic-apps/`
4. Copy the OSS skeleton contents *over* the existing tree (preserving `.git/` and `LICENSE`).
5. Run `git status` and curate carefully — make sure no stale files survive.
6. Update `README.md` and the docs to point to the new stack.
7. `git add . && git commit -m "feat: pivot to OSS stack (Wazuh + Keycloak + OpenRouter)"`
8. `git push`

Pros: history preserved, your existing stars/forks stay attached.
Cons: tangled commit history, recruiters who read the early commits will be confused.

---

## What about the Azure-side work you already did?

If you wrote any **KQL rules** during week 1, copy them into `detections/kql-archive/`. They're useful reference material when you write the Sigma equivalents — Sigma can compile to KQL, so you can verify the auto-generated KQL matches your hand-written version. That's a nice validation exercise.

If you wrote any **scope docs** or **CTI research** for Halcyon Care or UNC3944, those carry over unchanged. Move them into `docs/scope.md` and `docs/cti/scattered-spider.md`.

If you provisioned any **Azure resources** (resource group, Sentinel workspace, Entra dev tenant): delete them. Don't pay for what you won't use. Resource group delete handles the cascade.

---

## Done conditions

You are ready to start Week 2 when:

- [ ] Old Azure repo is archived (Path A) or rebranded (Path B)
- [ ] New `project-ouroboros-oss` repo is on GitHub
- [ ] GitHub Pages is set to build from Actions, and the site builds green on first push
- [ ] CI workflow runs and passes on the empty skeleton
- [ ] OpenRouter account exists, API key is in `.env`, spend cap is set
- [ ] Oracle Cloud account exists (provisioning the VM is Week 2's job)
- [ ] `pytest` passes locally
- [ ] Any salvageable scope/CTI docs from the Azure version have been moved to `docs/`

If all of those are checked, close the laptop. Sunday's playbook is Week 2.
