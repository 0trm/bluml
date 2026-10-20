---
name: launching-models
description: Takes a model that won offline to real users safely and decides from live evidence whether it stays. Chooses batch, online or a cascade behind the rule, with a fallback, fixes the input contract, proves training and serving compute the same features, tests what the model learned, then rolls out through shadow, canary and an online test whose decision rule is written before it starts, with a rehearsed rollback. Use when a model is about to replace a rule or an older model, when writing a launch or deploy plan, when choosing between batch and online serving, when an offline gain is offered as the reason to ship to everyone, or when designing the A/B test or interleaving test for a model.
---

# Launching models

An offline result is a hypothesis; live traffic is the experiment. The launch exists to run that experiment without hurting users, and to be able to take the model back in minutes.

Read `MODEL.md` first. The Evaluation section must show the model beats the rule at the operating point. If the evidence came from a random split, a single AUC, or features nobody screened, run `doubting-results` on it before planning anything: a launch plan built on a leaked number ships the leak.

```
- [ ] 1. Serving shape and fallback chosen
- [ ] 2. Input contract written and checked at the boundary
- [ ] 3. Training and serving features proven equal
- [ ] 4. Tests pass before any traffic
- [ ] 5. Rollout ladder with pass and stop conditions
- [ ] 6. Online test designed, decision rule written
- [ ] 7. Rollback rehearsed; monitors live
- [ ] 8. MODEL.md Launch section written
```

## 1. Choose the serving shape

- **Batch** (score on a schedule, store, look up): cheaper, simpler, easy to inspect and roll back, and a failed run leaves the last scores serving instead of an outage. The default unless the prediction needs facts known only at request time.
- **Online** (score per request): when the input exists only at request time (the basket at checkout, the current session), when what the user wants fades within the visit, or when most users are new and have no history to score in advance. It brings a latency budget, a feature service, and failure modes per request.
- **A cascade:** the rule, or a cheap model, settles the cases it is sure of, and only the rest reach the model. It cuts compute and latency, and keeps the rule where it was trusted. The model then sees only what the stage before it passes on: train and evaluate it on those cases, and re-check it whenever that stage changes.
- **Fallback:** what the product does when the model, a feature or the service fails. Usually the rule it replaced. Write it down and test it.

The shape changes the case in the Decision section of `MODEL.md`. Batch pays per scheduled run and adds no latency to the request. Online is sized for peak traffic, paid around the clock, and adds its latency to every request it serves. Set the latency budget from what latency costs the product metric, not only from the page's timeout. If the shape, the model's size or the measured latency differ from what the case assumed, recompute it before the rollout.

[reference/serving.md](reference/serving.md) compares the options with the Crash Course's static and dynamic inference, says when online pays off, and covers cascades.

## 2. Write the input contract

List every input the model takes with its type, unit, range and missing default. Check it where requests enter the service, reject or flag violations, and count them. Log the features as served (Rules of ML #29): the log is the training data for the next model and the evidence for parity.

## 3. Prove training and serving compute the same features

Read the training feature code and the serving code side by side, feature by feature: units, time windows and how fresh each value is, reference tables and when they were built, defaults for missing values, category maps, and whether any training window includes the outcome being predicted. Then prove it with data: take served requests, rebuild their features with the training code, and compare values and scores. Compare missing rates as well: a training table enriched upstream (fields filled in for reports) is fuller than what serving sees, so log inputs as they arrive and after processing. Any mismatch blocks the launch; fix it in shared code (Rules of ML #32), not with a patch on one side.

## 4. Test before any traffic

- Unit tests for each feature function, including edge cases (missing values, new categories, zero prices). Pipeline tests assert coarse properties (row counts, unique ids, columns and types at each step) rather than exact values, so a correct change does not break them.
- The exported model loads and reproduces offline scores on a fixed set of examples (Rules of ML #9).
- Behavioural tests on the trained model: changing a field that should not matter (a name, an id) leaves the score unchanged; changing one that should moves it the expected way (a higher price lowers the predicted conversion).
- Each output is read as the class it means: two versions of a model can number the same classes differently.
- Latency and memory under expected load, inside the budget.
- The score distribution on recent inputs looks like validation.
- The infrastructure is tested apart from the model: the pipeline works with a trivial model too (Rules of ML #5).

## 5. Climb the rollout ladder

| Step | What happens | Moves on when | Stops when |
|---|---|---|---|
| Shadow | The model scores live traffic; nothing uses the scores | Served features and scores match offline; flag rate as expected; no errors | Parity fails; scores drift from validation |
| Canary | 1 to 5% of traffic uses the model | Errors, latency and guardrails stay flat | Any guardrail breaks |
| Online test | A randomized share uses the model for a fixed duration | The decision rule says ship | The decision rule says stop, or a guardrail breaks |
| Full rollout | Everyone, with the old model kept warm | Monitors stay quiet | A monitor alerts; roll back |

Each step has an owner and a date. Expect each tenfold step in traffic to surface problems the step before did not, and watch the first hours after it. A request to "roll out to all users this week" gets the ladder anyway; say what fits in the week (usually shadow and canary) and when the decision can be made. [reference/rollout.md](reference/rollout.md) covers shadow comparisons, degrees of automation and keeping past versions warm.

## 6. Design the online test before it starts

Write down, before the first user sees the model:

- **Primary metric:** the product rung of the metric ladder (the Decision section), not the offline metric.
- **Guardrails:** latency, errors, revenue, complaints, and anything the model could make worse while improving the primary metric.
- **Randomization unit:** usually the user, so one person sees one variant.
- **Size and duration:** the smallest effect worth shipping, the sample that detects it, rounded up to whole weeks. The smallest effect worth shipping is the break-even gain from the case, on the primary metric, without the latency line: the test arm runs at the real latency, so its effect already includes that cost. When detecting the break-even would take too long, say what the test can detect and what stays unknown.
- **Decision rule:** ship, stop or extend, as a function of the primary metric's interval against the break-even gain, and the guardrails.
- **Checks:** the sample ratio matches the planned split; no peeking that changes the decision.

For rankers, interleaving finds a preference with far less traffic than an A/B test; follow it with an A/B test when the business metric must be measured. [reference/online-tests.md](reference/online-tests.md) has the sizing formula and the checks.

## 7. Rehearse the rollback; turn on monitors

The current model or rule stays deployed and selectable by configuration, a feature flag or a registry alias, never by a code change; keep several past versions deployable, not only the last. Name what triggers a rollback (a guardrail breach, contract violations above a rate, scores outside a band) and who pulls it. Rehearse it once before the canary. Monitors on inputs, outputs and outcomes must be live before users see the model: set them up with `monitoring-models`.

## 8. Write it down

Fill the Launch section of `MODEL.md`: serving shape and fallback, the latency measured on the serving path and the compute bill, input contract, parity evidence, rollout steps with dates and results, the online test design and its result next to the offline gain that predicted it, the rollback and its rehearsal. Tick the gate items that hold. When the decision rule says ship and rollout completes, write the case with the online effect in the Live section (replacing the latency estimate, which the effect now contains) and set the stage to live.

## Report

Lead with the go or no-go and what it rests on. If something blocks the launch, name it with file and line, then give the plan that gets from here to a decision, step by step with dates.

## Stop signs

- The offline gain comes from a random split, a leak or a metric the product does not use.
- Training and serving compute a feature differently, or parity was never checked.
- No rollback that works without a deploy.
- A test with no decision rule written before it started.
- Going from zero to everyone in one step.
