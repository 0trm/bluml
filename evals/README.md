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

<!-- eval-results -->
