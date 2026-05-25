# Week 13 — A/B Evaluation Harness

## Objectives

- A canonical fixture set of Wazuh alerts (`agent/eval/fixtures/alerts.jsonl`) with known ground truth
- The `eval/score.py` harness runs that fixture set against at least 4 models
- Results land in `metrics/eval-<ts>.csv`
- A Grafana panel reads the CSV and shows per-model accuracy

## Build the fixture set

You need ~25–50 alerts spanning the categories you care about:

- 8 identity (MFA fatigue, OAuth abuse, role bursts, etc.)
- 8 host (SUID creation, suspicious cron, file integrity)
- 6 network (SSH brute force, port scans, suspicious egress)
- 4 cloud (Keycloak admin events, client secret addition)
- 4 LLM-app (prompt injection variants, PII leak attempts)

For each alert, include a `_scenario_for_eval` field that maps to a row in `ground_truth.jsonl`. The harness joins on this to score techniques + actor + FP correctness.

## Saturday — fixture creation

Capture real alerts from your lab as you run scenarios. Don't hand-author — that risks circularity (you write alerts that flatter your prompt).

```bash
# Capture last N alerts from Wazuh as a JSONL
curl -k -s -u "$WAZUH_API_USER:$WAZUH_API_PASSWORD" \
  "https://localhost:55000/alerts?limit=50" \
  | jq -c '.data.affected_items[] | .' \
  > agent/eval/fixtures/alerts.jsonl

# Manually annotate each with the scenario it came from
```

## Sunday — run the harness across models

```bash
make agent-eval
# or:
python -m agent.eval.score --models nousresearch/hermes-3-llama-3.1-70b,anthropic/claude-haiku-4.5,openai/gpt-4o-mini,qwen/qwen-2.5-72b-instruct
```

Output CSV columns:

- `model_slug`, `model_family`
- `alert_id`, `expected_techniques`, `got_techniques`, `mitre_overlap_count`, `techniques_correct`
- `actor_correct`, `fp_calibrated`, `tuning_suggested`
- `category`, `severity`

## Grafana panel

Mount the CSV directory into Grafana as a static file source (the CSV plugin works), or push results to Loki as structured JSON for a richer panel.

Three panels worth building:

1. Per-model accuracy on MITRE techniques (bar chart)
2. Per-model FP-calibration (calibration plot)
3. Per-category accuracy heatmap

## Cost budget per eval run

Hermes 3 70B on 30 alerts ≈ $0.30. Running all four models ≈ $1.50 per full eval cycle. You can afford to re-run nightly during weeks 13–16 to track regressions as you tune prompts.

## Done conditions

- [ ] Fixture set of 25+ alerts with ground truth links
- [ ] Eval harness runs without errors across 4 models
- [ ] At least one CSV in `metrics/`
- [ ] Grafana panel showing per-model accuracy
- [ ] First A/B insight written up (e.g. "Hermes outperforms Haiku on identity but Haiku is better-calibrated on FPs")

## What this is worth on the CV

This week's deliverable is the single most portfolio-valuable artifact. It shows you can:

- Evaluate LLMs, not just call them
- Reason about cost / accuracy trade-offs
- Produce metrics rather than vibes

Put the CSV + Grafana screenshots in the writeup.
