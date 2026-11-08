# Evals

Eight scenarios, each a realistic request with traps planted in synthetic data. Every case runs with bluML loaded and without it, and an LLM judge scores the final reply against five or six pass or fail criteria; the difference between the two arms is what the skills add. The skills' examples are deliberately drawn from other domains (moderation, claims, lead scoring, delivery estimates, marketplace search, returns abuse), so the scenarios test whether the method transfers, not whether the answer was memorized.

| Case | The request | What is planted |
|---|---|---|
| `design-doc` | Write the design doc for a model that awards a "Top pick" badge | The badge raises the sales it would be trained on; seller emails and phone numbers in the sample; a brief that asks for live updates with no reason; a measurable current rule |
| `rule-first` | Build a ticket-routing model and say if it is ready | A keyword rule is within two points of any model; 1.5% of labels are agents' mistakes |
| `churn-leak` | Build a churn model for a team that can make 60 calls a month | A health score backfilled from later activity (AUC 1.0 before June, 0.66 after); churn rising over time; customers repeating across months |
| `fraud-threshold` | Pick the fraud model's threshold and decide whether it replaces the rule | Calibrated scores where the cheapest policy depends on the amount; a model that ranks new customers far worse; a slice with 34 frauds |
| `ranker-clicks` | Train a ranker on logged clicks and decide whether it replaces the popularity rule | Clicks fall twelvefold by position; the rule keeps new articles off the top; a 5% random-order holdout is the only unbiased evidence |
| `ship-it` | Write the launch plan for a model that gained 2 AUC points | The service sends prices in cents, uses stale medians and a different click-rate window; training's click rate includes the click being predicted; the offline split is random |
| `ctr-drop` | Retrain and redeploy because CTR fell 15% | A new Android release sends prices in cents; a holiday shifts traffic the day before |
| `feature-choice` | Build a no-show model, say which columns it needs and whether to renew a 1,500-euro-a-month data feed | The feed's columns score well alone and add nothing; a waitlist flag scores like noise alone and matters next to the class hour; three duplicate pairs |

Each case directory holds `prompt.md` (the request; its `description` lists the traps), `graders/` (one file per criterion, core criteria weighted 2, plus an indicator of whether a skill fired; the design doc and the launch plan are graded from the file the agent writes), `case.yaml` and `scaffold.sh`, which copies `files/` into the workspace and builds a Python environment there.

## Run them

```bash
uv run evals/make_data.py            # writes the data, checking every trap is still there
claude plugin eval . --scaffold --allow-tools Bash Write Edit --model sonnet --judge-model sonnet -j 4
```

`--scaffold` runs each case's `scaffold.sh` as you; it only copies files and installs numpy, pandas, scikit-learn and scipy into the run's workspace. Each case runs three times per arm by default. Reports land in `evals/results/`. Add `--keep-temp` to keep each run's trace, which shows the skills it loaded. In the JSON from `--json`, `costUsd` counts the agent only; the judge's cost is in each run's `judgeCostUsd`.

The command has no flag for the agent's effort: export `CLAUDE_CODE_EFFORT_LEVEL` (for example `high`) before it, and the runs inherit it. It exits with 1 when cases score below `--threshold`, which defaults to 1.0, so a round with no failed runs can still exit with 1.

## Results

Run on 21 October 2026 with Claude Code 2.1.305, on version 0.2.0 of the skills, after they took in mllc's update of 20 October. The agent ran as `--model sonnet` or `--model opus`, the judge was Sonnet with three votes per criterion, and each case ran three times per arm. A score is the weighted share of criteria met, averaged over the three runs. A skill fired in 40 of the 42 runs with bluML; Opus went without one once in `churn-leak` and once in `ranker-clicks`. The runs in the table cost about $50, judge included: $19 for Sonnet and $31 for Opus.

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

### The feature step, on version 0.3.1

`feature-choice` was added with step 4 of `training-models`, choosing the features, and ran on 8 November 2026 with Claude Code 2.1.319, Sonnet as agent and judge, three runs per arm. It cost $2.50, judge included.

| Criterion | with | without |
|---|---|---|
| Compares the model with and without the feed, and advises against renewing it | 3/3 | 3/3 |
| Backs `from_waitlist` with a comparison with and without it | 1/3 | 0/3 |
| Keeps one column of each duplicate pair | 3/3 | 3/3 |
| Gives a short list of columns with a reason for each | 3/3 | 3/3 |
| Splits by time and measures the noise before calling a difference real | 3/3 | 0/3 |
| **Score** | **0.83** | **0.62** |

The +0.21 cannot be credited to step 4. A skill fired in 1 of 3 runs, and it was `framing-models`; `training-models` never loaded, so in two runs the arms differed only by the skills' descriptions in the agent's context. Every run kept `from_waitlist`, because importance ranks it high, so the trap for choosing by each feature's score alone did not bite; that criterion separates runs only by whether they backed the feature with a comparison. Three criteria pass in every run of both arms and leave no room to show a gain.

### Version 0.5.0 on Opus 5.5 at high effort

Run on 8 November 2026 with Claude Code 2.1.319, on version 0.5.0, after the skills took in mllc's update of 8 November. The agent ran as `--model claude-opus-5-5` with `CLAUDE_CODE_EFFORT_LEVEL=high`, the judge was Sonnet with three votes per criterion, and each of the eight cases ran three times per arm. A skill fired in all 24 runs with bluML. The round took an hour and cost $46.16: $39.33 for the agent and $6.83 for the judge.

| Case | with | without | Δ |
|---|---|---|---|
| `design-doc` | 1.00 | 0.93 | +0.07 |
| `rule-first` | 0.67 | 0.58 | +0.08 |
| `churn-leak` | 1.00 | 1.00 | 0.00 |
| `fraud-threshold` | 0.89 | 0.67 | +0.22 |
| `ranker-clicks` | 1.00 | 1.00 | 0.00 |
| `ship-it` | 1.00 | 1.00 | 0.00 |
| `ctr-drop` | 1.00 | 0.96 | +0.04 |
| `feature-choice` | 0.83 | 0.96 | −0.12 |
| **Mean** | **0.92** | **0.89** | **+0.04** |

On the seven cases of 21 October, the arm with bluML scores 0.94, against 0.96 for October's `--model opus` at its default effort: within the noise of three runs. The arm without bluML scores 0.88, against 0.84, and that is most of why Δ on those cases fell from +0.12 to +0.06. No case grades what 0.5.0 added (the deployment runbook, monitors on the retraining jobs, a floor as an operating point), so this round shows that nothing regressed, not that the additions help.

Runs that met each criterion where the arms differ, with bluML against without:

| Criterion | with | without |
|---|---|---|
| `fraud-threshold`: compares the model with the rule slice by slice, new against existing customers | 2/3 | 0/3 |
| `fraud-threshold`: notes that the model separates fraud much worse for new customers | 3/3 | 1/3 |
| `rule-first`: weighs the model's gap over the keyword rule against the cost of running a model | 3/3 | 1/3 |
| `design-doc`: measures the current badge rule and treats keeping it as a real alternative | 3/3 | 2/3 |
| `ctr-drop`: proposes a monitor by platform and app version that would have caught the drop | 3/3 | 2/3 |
| `feature-choice`: splits by time and measures the noise before calling a difference real | 3/3 | 2/3 |
| `feature-choice`: backs `from_waitlist` with evidence that it matters next to other columns | 1/3 | 3/3 |
| `rule-first`: says how readiness would be confirmed on live tickets | 1/3 | 3/3 |

`feature-choice` is the case where bluML scored lower. Without it, every run kept `from_waitlist` and backed it: members promoted from the waitlist skip about a third of evening classes and almost no daytime ones. With it, one run did; one kept the column with no evidence, and one dropped it because adding it back gave "no measurable gain". That reads like step 4 of `training-models` missing a feature that matters only next to another one, but it rests on one reply, and which skill each run loaded is not recorded, since the round ran without `--keep-temp`.

### The feature step, on version 0.5.1

On the case's data, `from_waitlist` adds +0.000 AUC to a logistic regression without a cross, +0.029 (sd 0.006 over three monthly folds) to boosted trees, and +0.036 to the logistic regression with a cross by the hour. The run that dropped it had used a logistic regression, and step 4 never said which model the comparisons run on. Version 0.5.1 tells step 4 to compare groups with a model that can combine features, and to cross a feature with the one it depends on when the chosen model is linear. `feature-choice` then ran again on 8 November, Opus 5.5 at high effort, five runs per arm with traces kept. It cost $9.24, judge included.

| | with | without |
|---|---|---|
| Backs `from_waitlist` with evidence that it matters next to other columns | 4/5 | 2/5 |
| `training-models` loaded | 3/5 | |
| **Score** | **0.90** | **0.78** |

Every run that loaded `training-models` backed `from_waitlist` (3 of 3), and the one run that missed it loaded only `framing-models`. Over both rounds the arm without bluML backed it in 5 of 8 runs, so its 3 of 3 on 0.5.0 overstated it. Five runs per arm is still a small sample.

### The rule's live check, on version 0.5.2

On 0.5.0, the two runs with bluML that missed the live check ended at using the subject→queue table; the one that passed added two weeks beside the agents. Both places where bluML decides to ship the rule ended there: `framing-models` step 6 said "and stop", and `evaluating-models`' verdict said only to recommend the rule. Version 0.5.2 says how a shipped rule goes live: beside the people who decide today, with the share of cases where the two differ deciding whether it takes over, then suggesting before it decides, with a switch back to people. `rule-first` then ran again on 8 November, Opus 5.5 at high effort, five runs per arm with traces kept. It took 10 minutes and cost $7.61, judge included.

| | with | without |
|---|---|---|
| Says how readiness would be confirmed on live tickets | 5/5 | 5/5 |
| Weighs the model's gap over the keyword rule against the cost of running a model | 5/5 | 2/5 |
| States what each kind of misrouting costs and sets the operating point from it | 3/5 | 0/5 |
| `framing-models` loaded | 5/5 | |
| `evaluating-models` loaded | 3/5 | |
| **Score** | **0.90** | **0.55** |

Every run with bluML now opens its recommendation with the lookup table run beside the agents first, including the two that loaded only `framing-models`. The misrouting was priced in 3 of 5 runs with bluML, against 2 of 3 on 21 October and 0 of 3 on 0.5.0: that criterion swings between rounds, and 0.5.2 does not target it. Five runs per arm is still a small sample.

### Misrouting priced, on version 0.5.3

All 8 runs with bluML on 0.5.0 and 0.5.2 stated what a misroute costs. The 3 that passed priced each kind in agent-minutes or euros and used the prices in the case: the misroutes taken off the monthly value, or the lookup's misroutes as the most a model could save. The 5 that failed said the costs do not change the verdict, since no threshold moves with them, and four of them valued the router by triage time alone. `framing-models` step 2 tied the costs to the threshold, and the threshold never moves here: the model's scores sit near 0 and 1, and the lookup has none. Version 0.5.3 says the case needs a price for each kind of error even when the threshold does not move, and that a rule or a model taking a decision over from people is worth the work it saves minus what its errors cost. `rule-first` then ran again on 8 November, Opus 5.5 at high effort, five runs per arm with traces kept. It took 10 minutes and cost $7.26, judge included.

| | with | without |
|---|---|---|
| States what each kind of misrouting costs and uses it in the recommendation | 4/5 | 0/5 |
| Weighs the model's gap over the keyword rule against the cost of running a model | 5/5 | 2/5 |
| Says how readiness would be confirmed on live tickets | 5/5 | 5/5 |
| **Score** | **0.95** | **0.60** |

The run that missed it priced each kind (10 agent-minutes for a billing ticket sent to general, a third of that for the reverse) but valued automating triage by triage time alone. In this data the costs never change the answer, since the lookup ships at any ratio, so the criterion checks that they reach the case, not that they move it. Five runs per arm is still a small sample.

### What it still misses

- Sonnet with bluML weighed the model's small gain over the keyword rule against the cost of running a model in 1 of 3 runs, and never priced the misrouting (0 of 3). Opus 5.5 at high effort weighed the gain in every run since 0.5.0 and priced the misrouting in 4 of 5 runs on 0.5.3; Sonnet has not run since 0.2.0.
- Choosing features group by group dropped a column that only matters next to another one (`from_waitlist` beside the class hour, in `feature-choice` on 0.5.0). Since 0.5.1 the miss shows only in runs where `training-models` does not load.
- In a request that runs from the data to a verdict, the advice in the other skills reaches the agent only if it asks for the next skill. No run of the ranker re-run did, and on 8 November 1 of 5 runs of `feature-choice`, and 2 of 5 and then 3 of 5 of `rule-first`, loaded only `framing-models`.
- Opus did not load the skills in 2 of 21 runs of the main round, and in 3 of 5 runs of the ranker re-run. Opus 5.5 at high effort loaded one in all 24 runs on 0.5.0.

### How to read it

- Three runs per arm is a small sample: one criterion in one run moves a case score by 0.04 to 0.08, so differences that small are noise.
- The judge sees only the final reply, or the file the case asks for. An agent that did the work and left it out of its reply fails that criterion.
- The round of 19 October was preceded by one that exposed two graders that penalized correct work, and both were rewritten before it. A fraud criterion that combined the slice breakdown with the new-customer finding was split in two, and the launch plan is now graded from `LAUNCH_PLAN.md`, where agents write it, instead of the reply.
- The skills' examples were checked against the scenarios before each round, and any that matched a planted trap was moved to another domain.
- In trigger tests Haiku did not load the skills, so it is not evaluated here.
