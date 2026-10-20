# {model name}

{One sentence: what the model predicts, and the product decision it serves.}

| Stage | Owner | Threshold owner | Updated |
|---|---|---|---|
| framing | {who builds and runs it} | {who answers for the cost of each error} | {YYYY-MM-DD} |

Stages run framing, design, data, training, evaluation, launch, live, retired. Each section ends at a gate; a stage starts only when the gate before it is ticked, with the evidence linked. When work loops back, set the stage back and say why in the log.

## 1. Decision

- **What the product does with it:** {when the prediction says X, the product does Y; who or what acts}
- **When it predicts:** {the moment of prediction, and what is known at that moment}
- **What each error costs:** {a false positive costs ...; a false negative costs ...; any capacity limit, such as 40 demos a week}
- **The rule to beat:** {the rule or current system, and its number on recent data, in the product's unit}
- **The metric ladder:** {business metric} → {product metric} → {online proxy} → {offline metric}
- **Why a model:** {what the rule cannot do, or "the rule ships" and why}
- **The case:** {decisions per month, the expected gain over the rule (a range) and what one unit is worth; build cost; monthly cost: upkeep, pipelines, training compute, serving compute, paid calls, latency; net value per month, break-even gain, payback in months; the input that flips the answer}

Gate:
- [ ] The threshold owner agreed the decision and the error costs
- [ ] The rule's number is measured on recent data
- [ ] The expected gain clears the break-even gain, or the rule ships and this file stops here

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

- **Row:** {one row per entity per prediction time}
- **Label:** {the event, its window after the prediction time, when it becomes known and when it stops changing, and the rows it is missing for}
- **Split:** {train, validation and test windows, and why they mirror serving}

| Feature | As of | Source | Note |
|---|---|---|---|
| {name} | {its value at prediction time, or how it is lagged} | {table or service} | {owner, backfills, units} |

- **Leak screen:** {result, and what was dropped}
- **What the product put in the labels:** {what the current system showed or did that shaped who has a label}
- **Label source and quality:** {where labels come from (user reports, an existing system, annotators, rules); audit sample size; agreement between labellers}

Gate:
- [ ] Every feature exists, with this value, at prediction time
- [ ] The leak screen ran and every flag is explained
- [ ] The split mirrors serving, and training and serving build features with the same code
- [ ] Labels come from a named source, and a sample checked by hand agrees with them

## 4. Training

| Run | Model | Data version | Validation result | Note |
|---|---|---|---|---|
| {run id} | {baseline: base rate, the rule, a simple model} | {hash or snapshot} | {metric at the operating point} | |

- **Ceiling:** {the score when the model is fit and scored on its own training rows, and whether the learning curve still rises; against the break-even gain}
- **Chosen:** {run id, and why it beats the simpler ones by enough to be worth it}

Gate:
- [ ] Baselines are recorded next to the candidates, on the same validation rows
- [ ] Every run can be rebuilt from its record (code, data version, parameters, seed)

## 5. Evaluation

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
- [ ] The test window was used once, after every choice was made

## 6. Launch

- **Serving:** {batch or online, latency budget and the latency measured on the serving path, compute cost per month, the fallback when the model or a feature fails}
- **Input contract:** {each input with its unit and range, checked at the service}
- **Rollout:** {shadow, then canary, then the online test, then everyone; each step's pass and stop conditions, and its result}
- **Online test:** {primary metric, guardrails, duration, decision rule against the break-even gain, written before it starts; the result next to the offline gain that predicted it}
- **Rollback:** {how to switch back without a code change, what triggers it, when it was rehearsed}

Gate:
- [ ] Shadow traffic shows the served features and scores match the offline ones
- [ ] The rollback was rehearsed and monitors were live before users saw the model
- [ ] The online test's decision rule was written before it started, and its result is in

## 7. Live

| Monitor | Layer | Alert when | Owner |
|---|---|---|---|
| {name} | {system, inputs, outputs or outcomes} | {condition} | {who is paged} |

- **Freshness:** {how fast performance decays with model age, and the retrain schedule it sets}
- **Retrain gate:** {the newest days held out; the checks against the live model and a naive baseline; the operating point re-chosen from the owner's requirement; a failed check keeps the live model}
- **The case, live:** {net value per month from the online effect and the actual bill; date checked and next check; retire to the rule when it turns negative}
- **Incidents:** {date, cause, fix, the monitor added; one line each}

## Log

- {YYYY-MM-DD}: {what was decided, by whom, and the evidence}
