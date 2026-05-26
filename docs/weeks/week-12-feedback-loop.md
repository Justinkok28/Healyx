# Week 12 — Close the feedback loop

## Objectives

- Triage agent's `suggested_tuning` field gets surfaced into a workflow
- A "tuning queue" file (`detections/tuning-queue.jsonl`) accumulates proposed Sigma changes
- A human (you) reviews each suggestion and either applies it via PR or rejects with reason
- The red-team planner reads recent tuning activity and adjusts its next-round choices

## The loop, end-to-end

```
red attack → Wazuh alert → triage agent → suggested_tuning →
  → tuning-queue.jsonl → manual PR review →
  → detections/sigma/ updated → make compile-rules → Wazuh reloads →
  → red planner sees more rules caught → adjusts → next round
```

## Saturday — wire the tuning queue

In `agent/triage/main.py`, after persisting the incident, also append to the tuning queue if `suggested_tuning` is non-null:

```python
if result.suggested_tuning is not None:
    queue_path = Path("/var/log/healyx/tuning-queue.jsonl")
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a") as f:
        f.write(json.dumps({
            "alert_id": result.alert_id,
            "suggestion": result.suggested_tuning.model_dump(),
            "narrative": result.narrative,
            "ts": result.classified_at.isoformat(),
        }) + "\n")
```

Add a CLI tool — `scripts/review_tuning.py` — that:

1. Reads the queue
2. For each entry, shows the suggestion and asks Apply / Reject / Skip
3. On Apply: opens `detections/sigma/<rule_id>.yml` in `$EDITOR` for the user to patch
4. On Reject: prompts for a reason and writes to `detections/tuning-rejected.jsonl`

## Sunday — planner awareness

Modify `agent/redteam/main.py`'s `_read_recent_triage_summary` to also include:

- Which Sigma rule IDs have been tuned in the last 7 days
- Which scenarios were *caught* vs *missed* in the last session

The planner now has signal for what's worth re-attacking.

Add a section to the planner prompt:

> Recent tuning activity:
> - healyx-keycloak-mfa-fatigue-v1: tuned 2 days ago (narrowed threshold)
>
> If a rule has been recently tuned, prioritize re-running the corresponding scenario to test whether the tuning held.

## Done conditions

- [ ] Triage suggestions land in `tuning-queue.jsonl`
- [ ] `scripts/review_tuning.py` works as a CLI workflow
- [ ] At least one tuning suggestion has been applied as a real Sigma edit
- [ ] After applying it, the next red-team run produces a different (better) alert behavior
- [ ] Planner prompt is aware of recent tuning activity

## Pitfalls

- **LLM proposes tuning that drops detection entirely.** Always review. A "tune" can be a "deprecate" suggestion which silently disables coverage. The CLI tool should treat `change_type=deprecate` with extra friction.
- **Suggested patches don't apply cleanly.** Hermes is decent at YAML but not perfect. Expect ~50% of proposed `sigma_patch_yaml` blocks to need hand-edits before they apply.
