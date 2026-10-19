# Rollout

## Contents

- Shadow mode
- Canary
- Blue-green
- Degrees of automation
- Keeping the old model warm

## Shadow mode

The new model scores live requests next to the current system; its output is logged and never used. Shadow catches the failures offline evaluation cannot: features computed differently in serving, missing inputs, latency, and score distributions that differ from validation.

Compare, per request, over at least a full weekly cycle:

1. Each served feature against the same feature rebuilt by the training code for that request.
2. The model's score from the service against its offline score on the rebuilt features: they must match to rounding.
3. The share of requests the new model would act on, against validation and against the current system.
4. Where the new and current systems disagree: read a sample; disagreements are where the gain or the bug lives.

Shadow is the cheapest step in the ladder and the one most often skipped.

## Canary

Route 1 to 5% of traffic to the new model and watch system health and guardrails for hours to days. A canary detects breakage, not improvement: it is too small and too short to measure the product metric.

## Blue-green

Run the old (blue) and new (green) versions side by side and switch traffic between them at the router. Rollback is switching back. It needs capacity for both and a single switch everyone knows.

## Degrees of automation

A model can enter a human decision gradually, and each step is also a rollout step:

1. **Human only:** the model's output is logged, not shown (shadow).
2. **Assistance:** the model's suggestion is shown; the person decides (a suggested category, a highlighted claim).
3. **Partial automation:** the model decides when confident; the person decides the rest.
4. **Full automation.**

Partial automation is often the right end state for decisions with costly errors. The rate at which people override the model at each step is a live label.

## Keeping the old model warm

Until the new model has passed its online test and run clean for a while, the old one stays deployed, loaded and selectable by configuration or alias. A rollback that needs a build, a retrain or a person who knows the code is not a rollback.
