# The business case

A model replaces a rule only when the decisions it improves are worth more than everything it costs, every month, over the rule. This page lists what to count, how to price latency and compute, a worked case, and how the case changes from framing to retirement. The numbers in the worked case are illustrations, not benchmarks.

## Contents

- The three numbers
- What to count
- Latency
- Compute
- A worked case: marketplace search
- The case at each stage
- Questions for the owners

## The three numbers

```
value per month   = decisions per month × gain over the rule per decision × value of one unit
monthly cost      = upkeep + pipelines + training compute + decisions per month × cost per decision + latency cost
net per month     = value per month − monthly cost
break-even gain   = monthly cost ÷ (decisions per month × value of one unit)
payback, months   = build cost ÷ net per month          (never, when net ≤ 0)
```

- **Net per month** says whether the model pays at the expected gain.
- **The break-even gain** is the smallest gain over the rule, in the decision's unit, that covers the monthly cost. It is the bar for every later stage: the design doc's smallest change worth shipping, the verdict after evaluation, the online test's decision rule (without the latency line, which the test measures), and the retirement check.
- **Payback** says how long the build takes to repay. Compare it with how long the product will keep making this decision this way: a model that pays back in 18 months on a flow being redesigned next year does not pay.

Then recompute with the gain halved, and with the input you trust least off by a factor of two. Name the input that flips the answer; that is the question to settle before building.

For a classifier, the ceiling comes first and costs nothing: a perfect model saves at most the rule's error cost per month (its false positives and false negatives, priced as in the Decision section). When that ceiling is below the monthly cost, no model can pay, and the rule ships without anything being built.

## What to count

| Cost | Kind | How to estimate | Often forgotten |
|---|---|---|---|
| Build | Once | Engineer weeks at the team's loaded cost, for the data work, the model, serving, the launch and the review | The data pipeline and the launch take longer than the model |
| Labels | Once, then monthly | Price per label times labels needed; reviewer hours for an audit | Labels for new slices and for retraining keep costing |
| Upkeep | Monthly, fixed | A share of an engineer: on-call, monitors, incidents, reviewing each retrained version | The model's code is a small part of the system; the pipelines, configuration and monitoring around it carry most of the upkeep |
| Pipelines and storage | Monthly, fixed | Feature jobs, a feature store or cache, logs of served features | Logging served features is required for parity and the next training set |
| Training compute | Monthly, fixed | Cost per training run, searches included, times runs per month | A retrain schedule set by habit rather than by how fast quality decays |
| Serving compute | Per decision, or fixed | Cost per 1,000 predictions for batch; instances sized for peak traffic for online | Online capacity is paid for at peak, not at the average |
| Paid calls | Per decision | Vendor APIs, paid feature lookups, per-request licence fees | Calls made for requests that end in the fallback |
| Human work | Per decision | Reviewer minutes per flag, agent time per override | Already counted when the error costs include the cost of acting: count it once |
| Latency | Per request | The product metric lost per millisecond added, times requests | Paid on every request, including the ones the model gets right |
| The online test | Once | Users in the losing arm for the test's duration | A test sized too small to decide gets repeated |

Leave out costs the rule also has: the case is the model against the rule, not against nothing.

## Latency

A model inside a user-facing request adds time to it: feature lookups, scoring, network. Slower pages lose users on every request, not only on the ones whose decision changed, so a small delay on a busy page can cost more than the model gains.

1. Find what latency costs this product. The direct method is a slowdown test: delay the current page on purpose for a randomized share of users, and measure the product metric against the delay. Bing's slowdown tests found every 100 ms worth 0.6% of revenue, and the authors note the number holds for that site at that time (Kohavi et al., 2014): measure your own. Use the team's past slowdown tests when they exist. Without either, assume a cost per 100 ms, mark it as an assumption, and show the answer at twice that cost.
2. Measure what the model adds, at the median and the 95th percentile, on the real serving path: a benchmark of the model alone misses the feature lookups.
3. Price it: requests per month times the metric lost per request at that delay times the value of the metric.

Latency is the strongest argument for batch: a lookup of a precomputed score adds almost nothing. When the case only pays without the latency cost, score in batch and re-rank online, cache features, use a smaller model, or call the model only where it changes the decision. The case estimates the latency cost before anything is built; the online test measures it, inside the effect on the product metric, with latency as a guardrail. Once that effect is in, drop the estimated latency line from the case, or it is counted twice.

## Compute

- **Training:** cost per run (data size, hardware, hours) times runs per month, with hyperparameter searches counted as the runs they are. The retrain schedule comes from how fast quality decays with the model's age (`monitoring-models`); each retrain is also an engineer's review.
- **Serving, batch:** paid per scheduled run, roughly in proportion to the entities scored. Scoring every entity when only active ones are looked up is the usual waste.
- **Serving, online:** instances sized for peak traffic and the latency budget, paid around the clock. Cost per 1,000 predictions is the bill divided by predictions served, and it falls as traffic grows; quote both the bill and the unit cost.
- **A larger model** costs more on every line: training runs, serving hardware and latency. A gain that only the larger model reaches has to pay for all three.

Take prices from the team's own bill, not a price list: a month of the current service, a training run already done.

## A worked case: marketplace search

A marketplace orders search results by best-selling first. A ranker would re-order the top 100 listings per search, online, because the query is known only at request time.

| Input | Value | Source |
|---|---|---|
| Searches per month | 3,000,000 | Analytics |
| Purchases per search, with the rule | 4.0% | Analytics, last quarter |
| Margin per purchase | €6 | Finance |
| Expected gain over the rule | +2% purchases per search (relative), range +1% to +3% | Similar launches; an assumption until the online test |
| Build | 10 engineer weeks at €2,500 = €25,000 | Engineering manager |
| Upkeep | A fifth of an engineer, €2,200 a month | Team history |
| Pipelines and feature store | €800 a month | Current bill for similar jobs |
| Training compute | Weekly retrain at €50, €200 a month | One run already done |
| Serving compute | €0.15 per 1,000 searches, €450 a month | Load test |
| Latency added | 30 ms at the median | Load test on the serving path |
| Cost of latency | 1% of purchases per 100 ms | The team's slowdown test |

- **Value:** 120,000 purchases a month × €6 = €720,000 of margin; +2% is €14,400 a month.
- **Latency:** 30 ms costs 0.3% of purchases: €2,160 a month.
- **Monthly cost:** 2,200 + 800 + 200 + 450 + 2,160 = €5,810.
- **Net:** €8,590 a month. **Payback:** 25,000 ÷ 8,590 = 2.9 months.
- **Break-even gain:** 5,810 ÷ 720,000 = +0.8% purchases per search.

Sensitivity:

| Case | Gain | Latency | Net per month | Payback |
|---|---|---|---|---|
| Expected | +2% | 30 ms | €8,590 | 2.9 months |
| Gain halved | +1% | 30 ms | €1,390 | 18 months |
| Slow serving | +2% | 100 ms | €3,550 | 7 months |
| Both | +1% | 100 ms | −€3,650 | never |

The answer turns on the gain and the latency together. The design keeps the online path under 30 ms (candidates precomputed in batch, features cached), with latency as a guardrail in the online test. The test's arm runs at the real latency, so its measured effect already has the latency cost inside it: its bar is the break-even without that line, 3,650 ÷ 720,000 = +0.5% purchases per search. Counting the latency cost again would raise the bar to +0.8% and reject a model that pays.

## The case at each stage

| Stage | The gain comes from | What the case decides | Where it is written |
|---|---|---|---|
| Framing | An assumption, with a range; the ceiling for classifiers | Build, or ship the rule | Decision section of `MODEL.md` |
| Design | The feasibility numbers | The serving shape and the cost requirements | Cost section of the design doc |
| Evaluation | The measured offline gain and its interval | Whether the measured gain clears break-even | Evaluation section |
| Launch | The online test's effect on the product metric, with latency and compute as served | Ship, stop or extend | Launch section |
| Live | The online effect, the real bill, the rule's number re-measured | Keep, simplify or retire to the rule | Live section |

Each stage replaces an assumption with a measurement. When a stage changes an input (online instead of batch, a larger model, a slower path), recompute the case before going on.

## Questions for the owners

1. What is one unit of the decision worth: a sale, a ticket avoided, a fraud caught? Who signs off on that number?
2. How many decisions a month, and how is that changing?
3. What does an engineer week cost, loaded, and who maintains the model after launch?
4. What does the current serving and training setup cost per month, from the bill?
5. What does 100 ms cost on this page? Has anyone run a slowdown test?
6. How long will the product keep making this decision this way?
