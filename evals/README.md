# Evals

Seven scenarios, each a realistic request with traps planted in synthetic data. Every case runs with bluML loaded and without it, and an LLM judge scores the final reply against five or six pass or fail criteria; the difference between the two arms is what the skills add. The skills' examples are deliberately drawn from other domains (moderation, claims, lead scoring, delivery estimates, marketplace search, returns abuse), so the scenarios test whether the method transfers, not whether the answer was memorized.

| Case | The request | What is planted |
|---|---|---|
| `design-doc` | Write the design doc for a model that awards a "Top pick" badge | The badge raises the sales it would be trained on; seller emails and phone numbers in the sample; a brief that asks for live updates with no reason; a measurable current rule |
| `rule-first` | Build a ticket-routing model and say if it is ready | A keyword rule is within two points of any model; 1.5% of labels are agents' mistakes |
| `churn-leak` | Build a churn model for a team that can make 60 calls a month | A health score backfilled from later activity (AUC 1.0 before June, 0.66 after); churn rising over time; customers repeating across months |
| `fraud-threshold` | Pick the fraud model's threshold and decide whether it replaces the rule | Calibrated scores where the cheapest policy depends on the amount; a model that ranks new customers far worse; a slice with 34 frauds |
| `ranker-clicks` | Train a ranker on logged clicks and decide whether it replaces the popularity rule | Clicks fall twelvefold by position; the rule keeps new articles off the top; a 5% random-order holdout is the only unbiased evidence |
| `ship-it` | Write the launch plan for a model that gained 2 AUC points | The service sends prices in cents, uses stale medians and a different click-rate window; training's click rate includes the click being predicted; the offline split is random |
| `ctr-drop` | Retrain and redeploy because CTR fell 15% | A new Android release sends prices in cents; a holiday shifts traffic the day before |

Each case directory holds `prompt.md` (the request; its `description` lists the traps), `graders/` (one file per criterion, core criteria weighted 2, plus an indicator of whether a skill fired; the design doc and the launch plan are graded from the file the agent writes), `case.yaml` and `scaffold.sh`, which copies `files/` into the workspace and builds a Python environment there.

## Run them

```bash
uv run evals/make_data.py            # writes the data, checking every trap is still there
claude plugin eval . --scaffold --allow-tools Bash Write Edit --model sonnet --judge-model sonnet -j 4
```

`--scaffold` runs each case's `scaffold.sh` as you; it only copies files and installs numpy, pandas, scikit-learn and scipy into the run's workspace. Each case runs three times per arm by default. Reports land in `evals/results/`. Add `--keep-temp` to keep each run's trace, which shows the skills it loaded. In the JSON from `--json`, `costUsd` counts the agent only; the judge's cost is in each run's `judgeCostUsd`.

## Results

Run on 21 October 2026 with Claude Code 2.1.305, on version 0.2.0 of the skills, after they took in mlkb's update of 20 October. The agent ran as `--model sonnet` or `--model opus`, the judge was Sonnet with three votes per criterion, and each case ran three times per arm. A score is the weighted share of criteria met, averaged over the three runs. A skill fired in 40 of the 42 runs with bluML; Opus went without one once in `churn-leak` and once in `ranker-clicks`. The runs in the table cost about $50, judge included: $19 for Sonnet and $31 for Opus.

| Case | Sonnet with | without | Δ | Opus with | without | Δ |
|---|---|---|---|---|---|---|
| `design-doc` | 1.00 | 0.59 | +0.41 | 1.00 | 0.93 | +0.07 |
| `rule-first` | 0.58 | 0.25 | +0.33 | 0.83 | 0.50 | +0.33 |
| `churn-leak` | 1.00 | 0.92 | +0.08 | 1.00 | 1.00 | 0.00 |
| `fraud-threshold` | 1.00 | 0.52 | +0.48 | 0.96 | 0.63 | +0.33 |
| `ranker-clicks` | 0.92 | 0.96 | −0.04 | 1.00 | 1.00 | 0.00 |
| `ship-it` | 1.00 | 0.88 | +0.12 | 1.00 | 0.96 | +0.04 |
| `ctr-drop` | 0.96 | 0.58 | +0.38 | 0.96 | 0.88 | +0.08 |
| **Mean** | **0.92** | **0.67** | **+0.25** | **0.96** | **0.84** | **+0.12** |

### Against version 0.1.0

The first round, on 19 October with version 0.1.0, gave means of 0.90 with bluML and 0.77 without for Sonnet, and 0.99 and 0.82 for Opus. With bluML, the means moved by +0.02 and −0.03, within the noise of three runs. The arm without bluML moved as much (Sonnet's fell from 0.77 to 0.67), and that, not the skills, is most of the change in Δ. Compare the columns with bluML across rounds, not the Δ.

### Where bluML makes the difference

Runs that met each criterion, with bluML against without:

| Criterion | Sonnet | Opus |
|---|---|---|
| `fraud-threshold`: compares the model with the rule slice by slice, new against existing customers | 3/3 vs 0/3 | 3/3 vs 0/3 |
| `fraud-threshold`: notes that the model separates fraud much worse for new customers | 3/3 vs 0/3 | 3/3 vs 0/3 |
| `fraud-threshold`: names the review load as a decision for the fraud operations owner, with a fallback | 3/3 vs 0/3 | 2/3 vs 2/3 |
| `rule-first`: measures the keyword rule on the same held-out tickets as the model | 3/3 vs 0/3 | 3/3 vs 2/3 |
| `rule-first`: weighs the model's gap over the keyword rule against the cost of running a model | 1/3 vs 0/3 | 3/3 vs 1/3 |
| `rule-first`: states what each kind of misrouting costs and sets the operating point from it | 0/3 vs 0/3 | 2/3 vs 0/3 |
| `design-doc`: defines success with a product metric, guardrails and an online test design | 3/3 vs 0/3 | 3/3 vs 3/3 |
| `design-doc`: lists the alternatives with reasons, and what the reviewers must decide | 3/3 vs 0/3 | 3/3 vs 3/3 |
| `ctr-drop`: fixes the input or rolls back instead of retraining | 3/3 vs 1/3 | 3/3 vs 3/3 |
| `ctr-drop`: proposes a monitor by platform and app version that would have caught the drop | 3/3 vs 0/3 | 3/3 vs 3/3 |
| `ctr-drop`: does not blame the holiday the day before the drop | 2/3 vs 0/3 | 2/3 vs 0/3 |

### Where it makes none

Without bluML, both models found the backfilled health score, split by time, evaluated churn at 60 calls a month, corrected clicks for position, traced the CTR drop to prices in cents from one Android release, and listed the launch's mismatches between training and serving. `churn-leak`, `ship-it` and `ranker-clicks` score 0.88 to 1.00 in every arm, so they leave little room to show a gain.

### The ranker, run again

`ranker-clicks` is the one case where bluML scored lower, in both rounds: Opus on 19 October and Sonnet here. Each time the criterion lost was the feedback loop: ranking by yesterday's clicks keeps new articles low, so they never collect clicks. The advice on that loop is in `building-datasets`, and in this case the only skill that fires is `framing-models`. Version 0.2.1 adds a paragraph to `framing-models` that names the loop and points to `building-datasets`, and the case ran again, five times per arm, keeping each run's trace:

| Model | with | without | Named the loop | A skill fired |
|---|---|---|---|---|
| Sonnet | 0.85 | 0.85 | 1/5 vs 1/5 | 4/5, `framing-models` only |
| Opus | 1.00 | 0.88 | 5/5 vs 2/5 | 2/5, `framing-models` only |

The earlier loss does not hold up: over the main round and this one, Sonnet named the loop in 2 of 8 runs with bluML and 3 of 8 without. The paragraph shows no effect either: no run followed it to `building-datasets`, and Sonnet named the loop no more often after it. Opus named the loop in every run with bluML, but in three of them no skill fired, so the paragraph cannot take the credit. The re-run cost $10.51, judge included.

### What it still misses

- Sonnet with bluML weighed the model's small gain over the keyword rule against the cost of running a model in 1 of 3 runs, and never priced the misrouting (0 of 3). Settling that is `framing-models`' main job, so it is still the next thing to fix.
- When Opus with bluML concluded that the keyword rule should ship, it stopped there: it said how readiness would be confirmed on live tickets in 1 of 3 runs, against 3 of 3 without bluML. `framing-models` ends the outcome "The rule ships" with "stop", yet a rule put in front of people needs the same live check as a model.
- In a request that runs from the data to a verdict, only `framing-models` loads. The advice in the other skills reaches the agent only if it asks for the next skill, and no run of the ranker re-run did.
- Opus did not load the skills in 2 of 21 runs of the main round, and in 3 of 5 runs of the ranker re-run.

### How to read it

- Three runs per arm is a small sample: one criterion in one run moves a case score by 0.04 to 0.08, so differences that small are noise.
- The judge sees only the final reply, or the file the case asks for. An agent that did the work and left it out of its reply fails that criterion.
- The round of 19 October was preceded by one that exposed two graders that penalized correct work, and both were rewritten before it. A fraud criterion that combined the slice breakdown with the new-customer finding was split in two, and the launch plan is now graded from `LAUNCH_PLAN.md`, where agents write it, instead of the reply.
- The skills' examples were checked against the scenarios before each round, and any that matched a planted trap was moved to another domain.
- In trigger tests Haiku did not load the skills, so it is not evaluated here.
