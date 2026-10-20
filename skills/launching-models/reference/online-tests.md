# Online tests

The online test decides whether the model stays. Design it before launch, then follow the design.

## Contents

- The design, written first
- Sizing
- Checks while it runs
- Reading the result
- Interleaving for rankers
- When a model changes what it measures

## The design, written first

| Item | Example |
|---|---|
| Hypothesis | The new ranking raises clicks per visit on the home feed |
| Primary metric | Clicks per visit, per user, over the test |
| Guardrails | p95 latency, error rate, revenue per visit, share of visits with no click |
| Unit | User (cookie or account), so one person sees one variant |
| Split | 50/50, or 10/90 for a risky change |
| Minimum effect worth shipping | +2% clicks per visit |
| Duration | Whole weeks, at least two, long enough for the sample below |
| Decision rule | Ship if the primary metric's 95% interval is above zero and no guardrail is worse beyond its margin; stop if the interval is below zero or a guardrail breaks; otherwise keep the old model |

## Sizing

For a difference in means between two equal groups, at 5% significance and 80% power, each group needs about

`n = 16 × σ² / δ²`

users, where σ is the metric's standard deviation per user and δ the minimum effect in absolute terms. For a rate p, σ² = p(1 − p). Example: a click rate of 5% and a minimum relative lift of 5% (δ = 0.0025) need 16 × 0.0475 / 0.0025² ≈ 122,000 users per group. If that takes longer than the product can wait, raise the minimum effect, use a more sensitive metric, or use interleaving.

## Checks while it runs

- **Sample ratio:** the observed split matches the planned one (a chi-square test). A mismatch means the assignment or logging is broken; the result cannot be trusted until it is explained.
- **Guardrails:** watched daily; a breach stops the test.
- **No peeking that changes the decision:** looking at the primary metric daily and stopping on the first significant day inflates false wins. If early stopping is needed, use a sequential method and say so in the design.

## Reading the result

Report the primary metric's difference with its interval, the guardrails, and the sample ratio. Check novelty: compare the first and last week. Then follow the decision rule as written. A model that wins on its proxy and loses on the product metric loses (Rules of ML #39: launch decisions are a proxy for long-term goals, and a refused launch sends the objective back to framing).

Write the offline gain next to the online effect, test after test. An offline metric that predicts online results makes every later decision cheaper; one that stops predicting them needs fixing (the metric, the split, or a counterfactual estimate, in `building-datasets`, reference/product-bias.md) before the next offline win is trusted.

## Interleaving for rankers

For each request, merge the two rankings into one list (team-draft interleaving) and credit each click to the ranking that contributed the item. Preference shows within each request, so it needs far less traffic than an A/B test. It says which ranking users prefer, not by how much the business metric moves; follow a decisive interleaving result with an A/B test when the size of the effect matters.

## When a model changes what it measures

Some predictions change the outcome they predict: a longer delivery estimate reduces orders and so speeds up deliveries; a call list changes who churns. Measure the full ladder (conversion, on-time rate, cancellations, repeat orders), not the prediction error alone. A more accurate model can still lose money.
