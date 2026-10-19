---
name: monitoring-models
description: Keeps a live model honest. Sets monitors on system health, inputs, outputs and outcomes, decides how fresh the model must stay, and when a live number moves, finds the cause before choosing the fix (leave it, repair the input, align training and serving, retrain on clean data, or roll back), then writes the incident down. Use when a live model's metric, click rate, flag rate or scores change, when someone asks to retrain or redeploy because results got worse, when inputs or predictions drift, when serving and training scores disagree, when setting up monitoring or alerts for a model, when deciding how often to retrain, or when asking whether a live model still pays for itself or should be retired.
---

# Monitoring models

A broken service throws an error. A degraded model keeps returning confident, plausible answers while every dashboard stays green. Assume the live model is getting worse right now, and keep the instruments that would show it.

Read `MODEL.md` first: the Launch section says what was launched and with which contract; the Live section holds the monitors and past incidents.

## 1. Monitor four layers

| Layer | Watch | Catches |
|---|---|---|
| System | Latency, errors, throughput, fallback rate | A broken service |
| Inputs | Schema, missing rate, ranges, distribution against training, by segment (platform, app version, country, source) | Upstream changes, client bugs, unit changes, stale tables (Rules of ML #10) |
| Outputs | Score distribution, share of rows acted on, mix of the top of the list | A model reacting to bad inputs, or a serving bug |
| Outcomes | The label as it matures; the product metric | Real decay, and the world changing |

Outcomes matter most and arrive last; inputs and outputs are the early warning. Every monitor has a threshold, an owner and a place in the Live section of `MODEL.md`. Segment the input checks: most pipeline bugs live in one platform, version or source and are diluted in the total.

To compare live rows with training rows:

```bash
python scripts/drift.py training_sample.csv live.csv --by platform app_version --time ts --freq D
```

`scripts/` is in this skill's directory: use its full path. Any Python with numpy and pandas runs it; `uv run` installs them if missing. It reports PSI, missing-rate changes, out-of-range values and unseen categories, overall, per segment and per day, with the first day each column moved. [reference/monitors.md](reference/monitors.md) explains the statistics and how to set thresholds without drowning in alerts.

## 2. Decide how fresh the model must stay

Measure how quality decays with the model's age: train on data up to a date, score each following week, and plot the metric against weeks since training (Rules of ML #8). The retrain schedule comes from that curve, not from habit: retrain when the value lost to decay since the last version exceeds what a retrain costs in compute and review time. Every retrained version passes the same validation and launch checks before it replaces the live one.

## 3. When a number moves, find the cause first

Do not retrain, redeploy or roll back until the cause is named with evidence. Work through these in order:

1. **Is it real?** Logging or dashboard changes, late data, a holiday or a campaign, a change in the denominator.
2. **When did it start?** Find the first bad day or hour.
3. **Where is it?** Split the drop by segment and time: platform, app version, country, traffic source, model version. A drop concentrated in one segment is almost never the model's fault.
4. **Which layer moved first?** Inputs moved: a pipeline, client or upstream change. Outputs moved with steady inputs: the model or its serving. Outcomes moved with steady inputs and outputs: the world or the product around the model.
5. **What changed at that moment?** Releases, schema changes, upstream jobs, new data sources, pricing, campaigns.

Write the cause as one sentence with its evidence: "Since Monday 2 March the nightly job that refreshes `customer_history` has failed; history features for accounts created since then are missing and default to zero, and the model sends those accounts' returns to review at three times the usual rate."

[reference/diagnosis.md](reference/diagnosis.md) walks through a full diagnosis.

## 4. Fix by cause

| Cause | Fix | Do not |
|---|---|---|
| Broken input (units, schema, nulls, a stale table) | Fix the source or convert at the service boundary; add the contract check that would have caught it; exclude the bad period from future training | Retrain: the model would learn the bug as behaviour |
| Training and serving compute a feature differently | Move both to shared code; prove parity again | Patch one side |
| Inputs shifted, model still right for them | Leave it; watch outcomes | Retrain because a chart moved |
| The relationship changed (concept drift) | Retrain on recent clean data, validated on the newest window | Retrain on a window that includes broken data |
| A bad model version or serving bug | Roll back to the previous version | Debug in production while users see it |
| Expected seasonal or calendar shift | Leave it; annotate the dashboard | Page someone |

When a request asks to retrain and the diagnosis points elsewhere, say so plainly, show the evidence, and do the fix the cause calls for. If the person still wants the retrain, exclude the broken rows.

## 5. Watch for feedback loops

When the model's actions shape its next training data (rankings decide what gets clicked, calls decide who stays), keep a small random or untreated slice, and watch the diversity of what the model shows and acts on. A loop shows as fewer distinct items on top, fresh items never rising, or a positive rate that drifts with no outside cause.

## 6. Keep the case current

A model that paid at launch can stop paying: traffic falls, the bill grows, the rule gets better, the gain decays. Rerun the case in `MODEL.md` every quarter, and whenever the serving bill, the traffic or the rule changes, with live numbers: the online test's effect or a small holdout kept on the rule for the gain, the actual bill for compute, the latency measured on the serving path. Record the date and the result in the Live section. When net value turns negative (the live gain has fallen below the break-even gain), propose retiring the model to the rule: say so with the numbers, and on the owner's agreement set the stage to retired and write why in the log.

## 7. Write the incident down

For every incident, add one line to the Live section of `MODEL.md`: when it started, when it was detected, the cause, the fix, and the monitor added so it is caught sooner next time. For larger incidents, write a short review: timeline, cause, what detection missed, actions with owners.

## Stop signs

- "Retrain and redeploy" requested before anyone has looked at what changed.
- A drop concentrated in one platform, version or source.
- Inputs that changed at a release boundary.
- A model with no input monitors, or monitors on the total only.
- Training data for a retrain that includes the broken period.
