# Serving

## Contents

- Batch, online, on device
- Cascades
- Static and dynamic training
- Latency budgets
- Fallbacks

## Batch, online, on device

| Shape | How | Fits | Costs |
|---|---|---|---|
| Batch (static inference) | Score every entity on a schedule, store the results, look them up | Recommendations for every user, monthly call lists, nightly prices | Predictions are as stale as the schedule; entities unseen at scoring time get none |
| Online (dynamic inference) | Score each request when it arrives | Fraud at checkout, delivery estimates, search ranking with the query | A latency budget, a feature service, per-request failures to handle |
| On device | Ship the model to the phone or browser | Keyboard suggestions, offline features, private data | Size, battery, slow updates, versions in the wild |

Teams build online systems they did not need. Start with batch unless the prediction needs information that exists only at request time; a batch table is also easy to inspect, test and roll back, and when a run fails, yesterday's scores keep serving. Ask first whether the experience can wait for an asynchronous answer. A common hybrid scores candidates in batch and re-ranks the top ones online.

Online pays off when what the user wants depends on the moment and fades fast (the one item being shopped for, a trip, what to watch tonight), or when most users are new and have no history to score in advance, as after a launch in a new market. It costs more: work per request, often nothing cached to fall back on, and a service that must stay fast all day and night, with someone on call for it.

## Cascades

A cascade puts cheap stages in front of the model: limits and rules first, then a small model, then the costly one. Each stage settles the cases it is sure of and passes the rest on, so the costliest model sees the fewest cases. In one bot-detection system, hundreds of rules run in about 20 ms against about 50 ms for one model call, and settle 15% of traffic with the fewest false positives of any method there; the models see what is left (Yan, *Content Moderation & Fraud Detection*). Rankers work the same way: retrieval narrows millions of items to hundreds, quickly and coarsely, and the ranker scores only those.

For a model that replaces a rule, the first cascade is the rule itself: keep it where it is sure, and send the model the rest. Two consequences:

- The model sees only what the earlier stages pass on. Train and evaluate it on those cases, not on all rows.
- When an earlier stage changes (a new rule, a retrained filter), the model's inputs change with it. Re-check the model on the new pass-through, and give each stage an owner who announces changes.

## Static and dynamic training

A model trained once and served for months goes stale as the world moves; one retrained continuously needs monitoring of every new version and a way to stop a bad one. Most product models sit in between: retrain on a schedule set by how fast quality decays with model age (see `monitoring-models`), and validate each new version on the newest data before it replaces the old one.

## Latency budgets

Set the budget from the product (the page's total budget, the checkout's timeout) and split it: feature lookup, model, network. Measure the 95th and 99th percentiles under load, not the mean. When the budget is tight, cache features, precompute what does not depend on the request, use a smaller model, or score in batch and re-rank online. When a few inputs make up most of the traffic (the top search queries), cache their answers and score only the misses.

## Fallbacks

Every online model needs an answer when it cannot answer: the rule it replaced, the last good batch score, or a safe default. Decide per failure: model timeout, missing feature, input outside the contract. Count how often each fallback fires; a rising count is an incident.
