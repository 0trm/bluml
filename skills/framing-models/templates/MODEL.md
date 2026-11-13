# {model name}

{One sentence: what the model predicts, and the product decision it serves.}

| ID | Stage | Owner | Threshold owner | Updated |
|---|---|---|---|---|
| {project}/{model} | framing | {who builds and runs it} | {who answers for the cost of each error} | {YYYY-MM-DD} |

The ID is `{project}/{model}`: the repo or product area, then the model's short name, the same as its folder. It stays the same across versions; the model card adds the live run after `@`. Stages run framing, design, data, training, evaluation, launch, live, retired. Each section ends at a gate. The agent marks an item whose evidence is in place with `(holds: {evidence})`; only the owner ticks it. A stage starts when the owner has ticked the gate before it and said go. From exploration to the verdict, the owner takes each decision in the stage's notebook, after writing a reading and a pick and before opening the agent's recommendation, and it is copied here in the owner's words. When work loops back, set the stage back and say why in the log.

## 1. Decision

- **What the product does with it:** {when the prediction says X, the product does Y; who or what acts}
- **When it predicts:** {the moment of prediction, and what is known at that moment}
- **What each error costs:** {a false positive costs ...; a false negative costs ...; any capacity limit, such as 40 demos a week}
- **The rule to beat:** {the rule or current system, and its number on recent data, in the product's unit}
- **The metric ladder:** {business metric} → {product metric} → {online proxy} → {offline metric}
- **Why a model:** {what the rule cannot do, or "the rule ships", why, and how it goes live: beside the people who decide today, the share of cases where they differ that lets it take over, and the switch back}
- **The case:** {decisions per month, the expected gain over the rule (a range) and what one unit is worth; build cost; monthly cost: upkeep, pipelines, training compute, serving compute, paid calls, latency; net value per month, break-even gain, payback in months; the input that flips the answer}

Gate:
- [ ] The threshold owner agreed the decision and the error costs
- [ ] The rule's number is measured on recent data
- [ ] The expected gain clears the break-even gain, or the rule ships with its live check written and this file stops here

## 2. Design

- **Design doc:** {link, or "design in this section" for a small model}
- **Reviewers:** {names and roles; pre-review and formal review dates}
- **Decisions taken:** {what the review settled}
- **Open risks:** {what the review left open, and who watches each}

Gate:
- [ ] The design was pre-reviewed, then reviewed by the people who decide
- [ ] Alternatives, including keeping the rule, are written down with why each was rejected
- [ ] The review's decisions and open risks are recorded here

## 3. Data

- **Exploration:** {path to eda.ipynb; one line per decision it led to}
- **Table notebook:** {path to data.ipynb; the owner's decisions on the rows, the label, the split and the leak flags, dated}
- **Row:** {one row per entity per prediction time}
- **Label:** {the event, its window after the prediction time, when it becomes known and when it stops changing, and the rows it is missing for}
- **Split:** {train, validation and test windows, and why they mirror serving}

| Feature | As of | Source | Note | Why in |
|---|---|---|---|---|
| {name} | {its value at prediction time, or how it is lagged} | {table or service} | {owner, backfills, units} | {baseline, or the gain its group added and the run id; filled in training} |

- **Leak screen:** {result, and what was dropped}
- **What the product put in the labels:** {what the current system showed or did that shaped who has a label}
- **Label source and quality:** {where labels come from (user reports, an existing system, annotators, rules); audit sample size; agreement between labellers}

Gate:
- [ ] The exploration notebook has the owner's reading and an implication in every section, and every decision it led to is recorded here
- [ ] The owner decided the rows, the label and the split in data.ipynb
- [ ] Every feature exists, with this value, at prediction time
- [ ] The leak screen ran and every flag is explained
- [ ] The split mirrors serving, and training and serving build features with the same code
- [ ] Labels come from a named source, and a sample checked by hand agrees with them

## 4. Training

- **Notebook:** {path to train.ipynb; MLflow experiment}
- **Candidates and the comparison rule:** {one line per candidate card: assumption, serving cost, how it fails; the rule and tie-break the owner wrote, dated, before any fit}
- **Keep rule:** {the owner's rule for keeping a feature group, dated, before any feature run}

| Run | Model | Data version | Validation result | Note |
|---|---|---|---|---|
| {run id} | {baseline: base rate, the rule, a simple model} | {hash or snapshot} | {metric at the operating point} | |

- **Ceiling:** {the score when the model is fit and scored on its own training rows, and whether the learning curve still rises; against the break-even gain}
- **Chosen:** {run id, and why it beats the simpler ones by enough to be worth it}

Gate:
- [ ] The comparison rule and the keep rule were written before the runs they judge
- [ ] Baselines are recorded next to the candidates, on the same validation rows
- [ ] Every feature in the chosen model has a Why in line backed by a run
- [ ] Every run can be rebuilt from its record (code, data version, parameters, seed)

## 5. Evaluation

- **Notebook:** {path to eval.ipynb}
- **Operating point:** {threshold, top-k or quantile, and how the costs set it}
- **Against the rule:** {difference in the product's unit, with its interval, on the test window}
- **The case at the measured gain:** {net value per month at the gain and at both ends of its interval, against the break-even gain; any cost the build changed}
- **Slices:** {where the model loses to the rule, and the slices too small to judge}
- **Errors left:** {the largest groups of errors, and whether data or the model fixes them}
- **Test set:** {used on YYYY-MM-DD; times used}

Gate:
- [ ] The model beats the rule at the operating point, and the interval excludes no gain
- [ ] The measured gain clears the break-even gain
- [ ] No slice that matters does worse than the rule, or it has its own policy
- [ ] The test window was used once, after every choice was made and the owner said go

## 6. Launch

- **Serving:** {batch or online, latency budget and the latency measured on the serving path, compute cost per month, the fallback when the model or a feature fails}
- **Input contract:** {each input with its unit and range, checked at the service}
- **Rollout:** {shadow, then canary, then the online test, then everyone; each step's pass and stop conditions, and its result}
- **Online test:** {primary metric, guardrails, duration, decision rule against the break-even gain, written before it starts, or with gallop installed the link to the plan filed by designing-experiments; the result next to the offline gain that predicted it}
- **Rollback:** {how to switch back without a code change, what triggers it, when it was rehearsed}
- **Runbook:** {who approves the start and each widening of the rollout, the steps, where a version goes first, what to do when a deployment fails; link}

Gate:
- [ ] Shadow traffic shows the served features and scores match the offline ones
- [ ] The rollback was rehearsed and monitors were live before users saw the model
- [ ] The online test's decision rule was written before it started, and its result is in

## 7. Live

| Monitor | Layer | Alert when | Owner |
|---|---|---|---|
| {name} | {system, inputs, outputs, outcomes, or pipelines when it retrains on a schedule} | {condition} | {who is paged} |

- **Freshness:** {how fast performance decays with model age, and the retrain schedule it sets}
- **Retrain gate:** {the newest days held out; the checks against the live model and a naive baseline; the operating point re-chosen from the owner's requirement; a failed check keeps the live model}
- **The case, live:** {net value per month from the online effect and the actual bill; date checked and next check; retire to the rule when it turns negative}
- **Incidents:** {date, cause, fix, the monitor added; one line each}

## Log

- {YYYY-MM-DD}: {what was decided, by whom, and the evidence}
- {YYYY-MM-DD}: Deviation: {the rule, decision or setting changed, from what to what, the result seen before the change, and whether the owner approved it}
- {YYYY-MM-DD}: Open: {a decision taken working alone: the question, the options, the rule, the agent's pick and its evidence; for the owner to take}
