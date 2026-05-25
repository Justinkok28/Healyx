# Week 1 — Bootstrap

> 4–6 hours. The week you finished on Saturday in the Azure version. Sunday is the pivot day.

## Objectives

- Repo on GitHub with CI/CD scaffolding green
- Docs site published to GitHub Pages
- OpenRouter account funded with spend cap
- Local dev environment working (`pytest` and `ruff` pass)
- Old Azure repo archived

## Saturday (the bit you may already have done in some form)

This was originally the Azure scaffold day. In the OSS pivot, Saturday becomes:

1. Run through [`PIVOT_CHECKLIST.md`](../../PIVOT_CHECKLIST.md) Steps 1–5
2. CI green on the empty skeleton
3. GitHub Pages building from `docs/`

If you already wrote scope or CTI docs for the Azure version, move them into `docs/scope.md` and `docs/cti/` — they carry over unchanged.

## Sunday — accounts + local dev

1. Sign up for Oracle Cloud (Step 6 of pivot checklist) — start early, it can be slow
2. Sign up for OpenRouter, fund $10, set $20/month spend cap
3. Local Python env with `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   cd agent && uv venv && source .venv/bin/activate
   uv pip install -r requirements-dev.txt
   pytest -v
   ```
4. Test OpenRouter from the command line:
   ```bash
   curl https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "nousresearch/hermes-3-llama-3.1-70b",
       "messages": [{"role": "user", "content": "Reply with the JSON {\"ok\": true}"}]
     }'
   ```

## Done conditions

- [ ] New repo on GitHub, CI green, Pages building
- [ ] Old Azure repo archived (or rebranded per Path B)
- [ ] OpenRouter key in `.env`, spend cap set
- [ ] Oracle account exists (provisioning is Week 2's job)
- [ ] `pytest` and `ruff` pass locally

## Common pitfalls

- **OpenRouter spend cap not set.** Set it in the OpenRouter dashboard *before* you hand the API key to the red-team planner. The env var is a reminder, not the enforcement.
- **`.env` committed.** Triple-check `.gitignore` lists `.env`. Run `git status` before every commit this week.
- **CI failing on placeholder tests.** Re-read the failure — usually `ruff` flagged a trivial issue. Fix in place; don't disable rules.

## Next week

Week 2 is the Oracle VM. Read `week-02-oracle-vm.md` before Saturday so you know what hardware decisions you'll be making.
