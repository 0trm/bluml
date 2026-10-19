# Serving

## Contents

- Batch, online, on device
- Static and dynamic training
- Latency budgets
- Fallbacks

## Batch, online, on device

| Shape | How | Fits | Costs |
|---|---|---|---|
| Batch (static inference) | Score every entity on a schedule, store the results, look them up | Recommendations for every user, monthly call lists, nightly prices | Predictions are as stale as the schedule; entities unseen at scoring time get none |
| Online (dynamic inference) | Score each request when it arrives | Fraud at checkout, delivery estimates, search ranking with the query | A latency budget, a feature service, per-request failures to handle |
| On device | Ship the model to the phone or browser | Keyboard suggestions, offline features, private data | Size, battery, slow updates, versions in the wild |

Teams build online systems they did not need. Start with batch unless the prediction needs information that exists only at request time; a batch table is also easy to inspect, test and roll back. A common hybrid scores candidates in batch and re-ranks the top ones online.

## Static and dynamic training

A model trained once and served for months goes stale as the world moves; one retrained continuously needs monitoring of every new version and a way to stop a bad one. Most product models sit in between: retrain on a schedule set by how fast quality decays with model age (see `monitoring-models`), and validate each new version on the newest data before it replaces the old one.

## Latency budgets

Set the budget from the product (the page's total budget, the checkout's timeout) and split it: feature lookup, model, network. Measure the 95th and 99th percentiles under load, not the mean. When the budget is tight, cache features, precompute what does not depend on the request, use a smaller model, or score in batch and re-rank online.

## Fallbacks

Every online model needs an answer when it cannot answer: the rule it replaced, the last good batch score, or a safe default. Decide per failure: model timeout, missing feature, input outside the contract. Count how often each fallback fires; a rising count is an incident.
