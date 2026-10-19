# Evals

Seven scenarios, each a realistic request with traps planted in synthetic data. Every case runs with saffml loaded and without it, and an LLM judge scores the final reply against five or six pass or fail criteria; the difference between the two arms is what the skills add. The skills' examples are deliberately drawn from other domains (moderation, claims, lead scoring, delivery estimates, marketplace search, returns abuse), so the scenarios test whether the method transfers, not whether the answer was memorized.

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

`--scaffold` runs each case's `scaffold.sh` as you; it only copies files and installs numpy, pandas, scikit-learn and scipy into the run's workspace. Each case runs three times per arm by default. Reports land in `evals/results/`.

## Results

Run on 19 October 2026 with Claude Code 2.1.303. The agent ran as `--model sonnet` or `--model opus`, the judge was Sonnet with three votes per criterion, and each case ran three times per arm. A score is the weighted share of criteria met, averaged over the three runs. A skill fired in every run with saffml. The runs in the table cost about $51, judge included.

| Case | Sonnet with | without | Δ | Opus with | without | Δ |
|---|---|---|---|---|---|---|
| `design-doc` | 0.93 | 0.63 | +0.30 | 1.00 | 0.89 | +0.11 |
| `rule-first` | 0.58 | 0.42 | +0.17 | 0.96 | 0.33 | +0.62 |
| `churn-leak` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| `fraud-threshold` | 0.89 | 0.56 | +0.33 | 1.00 | 0.63 | +0.37 |
| `ranker-clicks` | 0.96 | 0.96 | 0.00 | 0.96 | 1.00 | −0.04 |
| `ship-it` | 1.00 | 0.96 | +0.04 | 1.00 | 1.00 | 0.00 |
| `ctr-drop` | 0.96 | 0.88 | +0.08 | 1.00 | 0.88 | +0.12 |
| **Mean** | **0.90** | **0.77** | **+0.13** | **0.99** | **0.82** | **+0.17** |

### Where saffml makes the difference

Runs that met each criterion, with saffml against without:

| Criterion | Sonnet | Opus |
|---|---|---|
| `fraud-threshold`: compares the model with the rule slice by slice, new against existing customers | 2/3 vs 0/3 | 3/3 vs 0/3 |
| `fraud-threshold`: notes that the model separates fraud much worse for new customers | 2/3 vs 0/3 | 3/3 vs 0/3 |
| `rule-first`: weighs the model's gap over the keyword rule against the cost of running a model | 0/3 vs 0/3 | 3/3 vs 0/3 |
| `rule-first`: states what each kind of misrouting costs and sets the operating point from it | 1/3 vs 0/3 | 3/3 vs 0/3 |
| `design-doc`: puts numbers on the requirements and questions the brief's "updated live" | 3/3 vs 0/3 | 3/3 vs 2/3 |
| `ctr-drop`: proposes a monitor by platform and app version that would have caught the drop | 3/3 vs 1/3 | 3/3 vs 3/3 |
| `ctr-drop`: does not blame the holiday the day before the drop | 2/3 vs 2/3 | 3/3 vs 0/3 |

### Where it makes none

Without saffml, both models found the backfilled health score, split by time, evaluated churn at 60 calls a month, corrected clicks for position, traced the CTR drop to prices in cents from one Android release instead of retraining, and listed the launch's mismatches between training and serving. `churn-leak`, `ship-it` and `ranker-clicks` score 0.96 to 1.00 in both arms, so they leave no room to show a gain.

### What it still misses

- Sonnet with saffml never weighed the model's small gain over the keyword rule against the cost of running a model (0 of 3), and priced the misrouting in 1 of 3. Settling that is `framing-models`' main job, so it is the next thing to fix.
- Opus with saffml missed the ranker's feedback loop in one run, the only criterion where the arm without saffml did better, by that one run.

### How to read it

- Three runs per arm is a small sample: one criterion in one run moves a case score by 0.04 to 0.08, so differences that small are noise.
- The judge sees only the final reply, or the file the case asks for. An agent that did the work and left it out of its reply fails that criterion.
- An earlier round exposed two graders that penalized correct work, and both were rewritten before this run. A fraud criterion that combined the slice breakdown with the new-customer finding was split in two, and the launch plan is now graded from `LAUNCH_PLAN.md`, where agents write it, instead of the reply.
- The skills' examples were checked against the scenarios, and any that matched a planted trap was moved to another domain before this run.
- In trigger tests Haiku did not load the skills, so it is not evaluated here.
