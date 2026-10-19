---
name: launching-models
description: Takes a model that won offline to real users safely and decides from live evidence whether it stays. Chooses batch or online serving with a fallback, fixes the input contract, proves training and serving compute the same features, then rolls out through shadow, canary and an online test whose decision rule is written before it starts, with a rehearsed rollback. Use when a model is about to replace a rule or an older model, when writing a launch or deploy plan, when choosing between batch and online serving, when an offline gain is offered as the reason to ship to everyone, or when designing the A/B test or interleaving test for a model.
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

- **Batch** (score on a schedule, store, look up): cheaper, simpler, easy to inspect and roll back. The default unless the prediction needs facts known only at request time.
- **Online** (score per request): when the input exists only at request time (the basket at checkout, the current session). It brings a latency budget, a feature service, and failure modes per request.
- **Fallback:** what the product does when the model, a feature or the service fails. Usually the rule it replaced. Write it down and test it.

[reference/serving.md](reference/serving.md) compares the options with the Crash Course's static and dynamic inference.

## 2. Write the input contract

List every input the model takes with its type, unit, range and missing default. Check it where requests enter the service, reject or flag violations, and count them. Log the features as served (Rules of ML #29): the log is the training data for the next model and the evidence for parity.

## 3. Prove training and serving compute the same features

Read the training feature code and the serving code side by side, feature by feature: units, time windows and how fresh each value is, reference tables and when they were built, defaults for missing values, category maps, and whether any training window includes the outcome being predicted. Then prove it with data: take served requests, rebuild their features with the training code, and compare values and scores. Any mismatch blocks the launch; fix it in shared code (Rules of ML #32), not with a patch on one side.

## 4. Test before any traffic

- Unit tests for each feature function, including edge cases (missing values, new categories, zero prices).
- The exported model loads and reproduces offline scores on a fixed set of examples (Rules of ML #9).
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

Each step has an owner and a date. A request to "roll out to all users this week" gets the ladder anyway; say what fits in the week (usually shadow and canary) and when the decision can be made. [reference/rollout.md](reference/rollout.md) covers shadow comparisons and degrees of automation.

## 6. Design the online test before it starts

Write down, before the first user sees the model:

- **Primary metric:** the product rung of the metric ladder (the Decision section), not the offline metric.
- **Guardrails:** latency, errors, revenue, complaints, and anything the model could make worse while improving the primary metric.
- **Randomization unit:** usually the user, so one person sees one variant.
- **Size and duration:** the smallest effect worth shipping, the sample that detects it, rounded up to whole weeks.
- **Decision rule:** ship, stop or extend, as a function of the primary metric's interval and the guardrails.
- **Checks:** the sample ratio matches the planned split; no peeking that changes the decision.

For rankers, interleaving finds a preference with far less traffic than an A/B test; follow it with an A/B test when the business metric must be measured. [reference/online-tests.md](reference/online-tests.md) has the sizing formula and the checks.

## 7. Rehearse the rollback; turn on monitors

The current model or rule stays deployed and selectable by configuration, a feature flag or a registry alias, never by a code change. Name what triggers a rollback (a guardrail breach, contract violations above a rate, scores outside a band) and who pulls it. Rehearse it once before the canary. Monitors on inputs, outputs and outcomes must be live before users see the model: set them up with `monitoring-models`.

## 8. Write it down

Fill the Launch section of `MODEL.md`: serving shape and fallback, input contract, parity evidence, rollout steps with dates and results, the online test design and its result, the rollback and its rehearsal. Tick the gate items that hold. When the decision rule says ship and rollout completes, set the stage to live.

## Report

Lead with the go or no-go and what it rests on. If something blocks the launch, name it with file and line, then give the plan that gets from here to a decision, step by step with dates.

## Stop signs

- The offline gain comes from a random split, a leak or a metric the product does not use.
- Training and serving compute a feature differently, or parity was never checked.
- No rollback that works without a deploy.
- A test with no decision rule written before it started.
- Going from zero to everyone in one step.
