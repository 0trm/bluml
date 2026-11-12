# Delivery estimate

Predicts how long an order will take to arrive, to show "arrives in 25 to 35 minutes" at checkout.

> A worked example: a made-up food delivery startup, written the way the bluML skills fill `MODEL.md`. Every number is illustrative.

| Stage | Owner | Threshold owner | Updated |
|---|---|---|---|
| live | Ana (ML engineer) | Marc (product manager, checkout), with operations | 2026-10-12 |

Stages run framing, design, data, training, evaluation, launch, live, retired. Each section ends at a gate. The agent marks an item whose evidence is in place with `(holds: {evidence})`; only the owner ticks it. A stage starts when the owner has ticked the gate before it and said go. From exploration to the verdict, the owner takes each decision in the stage's notebook, after writing a reading and a pick and before opening the agent's recommendation, and it is copied here in the owner's words. When work loops back, set the stage back and say why in the log.

## 1. Decision

- **What the product does with it:** shows a 10-minute window at checkout, whose upper end is the promise.
- **When it predicts:** when the customer reaches checkout. Known: the restaurant, its recent prep times, the queue of open orders, distance, time, weather, idle couriers nearby. Unknown: which courier takes the order, the actual prep time, the route.
- **What each error costs:** late is worse than early. An order later than the promise is a "where is my order" ticket (about €4 of support time) and lowers the chance of a repeat order; an early one costs nothing. A padded promise loses checkouts: about 1% of conversions per extra 5 minutes shown.
- **The rule to beat:** the restaurant's average prep time plus distance over the average courier speed. Last quarter it was on time for 71% of orders and late by more than 10 minutes for 9%.
- **The metric ladder:** repeat orders at 30 days → share of orders inside the promise → "where is my order" tickets and checkout conversion → pinball loss at the promised quantile on later orders.
- **Why a model:** prep times swing with the restaurant's queue and couriers with weather and hour; a hand-written rule cannot follow both.
- **The case:** 1.2 million orders a month. Expected gain over the rule: +8 points on time (range +5 to +11), so 96,000 fewer late orders a month. One late order in eight becomes a €4 ticket, so each late order avoided is worth €0.50: €48,000 a month (€30,000 to €66,000). Repeat orders are left out, as upside for the online test to measure. Build: 14 engineer weeks (Ana 10, data platform 3, routing 1) at €2,500, €35,000. Every month: €2,700 of upkeep (a quarter of Ana's time), €600 to log live features, €150 of training compute (a monthly retrain and its search), €1,400 to serve and cache features (sized for 300 checkouts a second at peak), and €1,200 of latency (the service adds about 20 ms at checkout; checkout's 2025 slowdown test lost 0.2% of checkouts per 100 ms, so 480 orders at €2.50 margin). Total €6,050. Net €41,950 a month; break-even at 1 point of on-time rate; payback under a month. It still pays at the low end of the gain (net €23,950) and with a quarter of Q1's ticket rate.

Gate:
- [x] The threshold owner agreed the decision and the error costs (Marc, 2026-06-02)
- [x] The rule's number is measured on recent data (71% on time, Q2)
- [x] The expected gain clears the break-even gain (+8 points expected, break-even 1 point)

## 2. Design

- **Design doc:** [DESIGN.md](DESIGN.md)
- **Reviewers:** Joan (staff engineer, routing), Priya (data platform), Marc (product); pre-review 2026-06-09, review 2026-06-16
- **Decisions taken:** online serving with the rule as fallback; the promise is a quantile, chosen by an online test between P70, P80 and P90; live queue and courier features are logged at serving time and become the training data
- **Open risks:** new cities have no prep history (they keep the rule's estimate); the promise changes order volume, so the online test decides, not offline error

Gate:
- [x] The design was pre-reviewed, then reviewed by the people who decide
- [x] Alternatives, including keeping the rule, are written down with why each was rejected
- [x] The review's decisions and open risks are recorded here

## 3. Data

- **Exploration:** `eda.ipynb`, read by Ana and Marc on 2026-06-05. Train from March: a tracking fix on 2026-02-24 moved drop-off times by about 2 minutes, a step the chart puts on the release day. Delivery times have a long right tail in rain and on stacked orders, which points to a quantile loss.
- **Table notebook:** `data.ipynb`, decided by Ana on 2026-07-30: the split below, cancelled orders counted apart in every slice, and the three post-checkout fields out (see the leak screen).
- **Row:** one order at checkout.
- **Label:** minutes from checkout to delivery. Known within the hour and final once recorded. Missing for cancelled orders (4%), which cluster when things go badly; they are kept as a separate count and checked in every slice.
- **Split:** train March to July, validate August, test September, by checkout time; restaurants that joined after July are reported separately.

| Feature | As of | Source | Note | Why in |
|---|---|---|---|---|
| Restaurant prep time, median of the last 14 days | Checkout, from orders already delivered | orders table | Owner: data platform | In the simple model (r02); removing the restaurant group costs 0.9 in pinball@0.8 (r08) |
| Open orders at the restaurant | Checkout | live queue service | Logged at serving time | Live load group, with idle couriers: removing it costs 0.6 (r08) |
| Distance by road | Checkout | routing service | Kilometres | In the simple model (r02); removing the trip group costs 1.1 (r08) |
| Idle couriers within 2 km | Checkout | courier service | Logged at serving time | Live load group: removing it costs 0.6 (r08) |
| Hour, weekday, rain | Checkout | calendar, weather feed | | Context group: removing it costs 0.4 (r08) |

- **Leak screen:** `courier_id`, `actual_prep_minutes` and `wait_at_restaurant` dropped: all written after checkout. No other flags.
- **What the product put in the labels:** the promise itself changes behaviour: optimistic promises bring order surges that slow couriers. Measured in the online test, not offline.
- **Label source and quality:** checkout time from the order system, drop-off time from the courier app. 200 orders checked against courier GPS; 3 timestamps wrong, from manual completions.

Gate:
- [x] The exploration notebook has the owner's reading and an implication in every section, and every decision it led to is recorded here
- [x] The owner decided the rows, the label and the split in data.ipynb (Ana, 2026-07-30)
- [x] Every feature exists, with this value, at prediction time
- [x] The leak screen ran and every flag is explained
- [x] The split mirrors serving, and training and serving build features with the same code
- [x] Labels come from a named source, and a sample checked by hand agrees with them (197 of 200 against GPS)

## 4. Training

- **Notebook:** `train.ipynb`; MLflow experiment `delivery-eta`, each run tagged with its step and holding its charts.
- **Candidates and the comparison rule:** linear quantile regression (assumes prep and distance add up; the cheapest to serve; fails when the queue and the weather interact) and gradient-boosted trees with a quantile loss (assumes enough orders per restaurant to learn interactions; about 20 ms to serve; fails on restaurants with little history). The rule, written by Ana on 2026-07-31 before any fit: the lowest pinball@0.8 on August wins when it beats the next by more than the spread across weekly folds; the simpler model wins a tie.
- **Keep rule:** written by Ana on 2026-08-03 before any feature run: keep a group whose removal costs more than the spread across weekly folds (0.3 in pinball@0.8).

| Run | Model | Data version | Validation result | Note |
|---|---|---|---|---|
| r01 | The rule | orders-0731 | pinball@0.8 6.9; on time 71% | Baseline |
| r02 | Linear quantile regression, 5 features | orders-0731 | pinball@0.8 5.6; on time 78% | Simple model |
| r07 | Gradient-boosted trees, quantile loss at 0.8 | orders-0731 | pinball@0.8 4.8; on time 80% | Chosen |
| r08 | r07 without each feature group in turn | orders-0731 | pinball@0.8 worse by 0.9 (restaurant), 0.6 (live load), 1.1 (trip), 0.4 (context) | Ablation; every group clears the keep rule |

- **Ceiling:** fit and scored on its own training rows, r07 is on time for 86%, well past the rule plus the 1-point break-even. Trained on the latest half of the months, it scores pinball@0.8 5.1 on validation, against 4.8 on all five: more data still helps.
- **Dropped:** straight-line distance, a near-duplicate of distance by road (rank correlation 0.96); road distance stayed, since the routing service already serves it.
- **Chosen:** r07, by Ana on 2026-08-19 under the comparison rule. It beats the linear model by more than the spread across weekly folds (0.3), and both beat the rule.

Gate:
- [x] The comparison rule and the keep rule were written before the runs they judge
- [x] Baselines are recorded next to the candidates, on the same validation rows
- [x] Every feature in the chosen model has a Why in line backed by a run
- [x] Every run can be rebuilt from its record (code, data version, parameters, seed)

## 5. Evaluation

- **Notebook:** `eval.ipynb`
- **Operating point:** the 80th percentile as the upper end of the window, agreed with Marc; the online test chooses between the 70th, 80th and 90th.
- **Against the rule:** on September, on time 80% against 71% (difference +9 points, 95% interval +8 to +10); late by more than 10 minutes 3% against 9%.
- **The case at the measured gain:** +9 points is €54,000 a month of tickets avoided (€48,000 to €60,000 across the interval) against €6,050 of monthly cost: net €47,950 (€41,950 to €53,950). The load test confirmed the 20 ms the case assumed.
- **Slices:** peak hours and rain hold their gain. Restaurants with under two weeks of history: 74% on time, against the rule's 70%, interval crossing zero, so they keep the rule's estimate until they have two weeks of orders. Long trips (over 6 km): 49 late orders, too small to judge.
- **Errors left:** most late orders are restaurants whose queue jumps after checkout (a feature for orders placed in the next 5 minutes is not available at checkout), and couriers who stack two orders.
- **Test set:** used on 2026-08-20, once.

Gate:
- [x] The model beats the rule at the operating point, and the interval excludes no gain
- [x] The measured gain clears the break-even gain (+8 points at the interval's low end, against 1)
- [x] No slice that matters does worse than the rule, or it has its own policy
- [x] The test window was used once, after every choice was made and the owner said go

## 6. Launch

- **Serving:** online, inside a 60 ms budget; 20 ms added at the median on the serving path; €1,400 a month to serve and cache features. The rule is the fallback when a live feature times out (0.4% of requests in shadow).
- **Input contract:** distance 0 to 25 km, queue 0 to 60 orders, prep median 3 to 90 minutes; violations go to the fallback and are counted.
- **Rollout:** shadow for 7 days (served features and scores matched offline to rounding); canary on 2% for 2 days; online test for 4 weeks; everyone from 2026-09-28.
- **Online test:** arms P70, P80 and P90 against the rule, randomized by customer. Primary metric: repeat orders at 30 days. Guardrails: checkout conversion, cancellations, tickets. Tickets avoided already pay for the model, so the bar for repeat orders is no loss, not a gain. Decision rule written 2026-08-25: ship the arm with the highest repeat rate whose conversion is within 1% of the rule's. Result: P80 shipped (repeat orders +2.1%, interval +0.6 to +3.6; conversion -0.4%). Offline it gained 9 points on time; in the test it gained 8 (79% against 71%).
- **Rollback:** a config flag selects the rule or the model version; rehearsed 2026-08-27; triggered by p99 latency above 60 ms for 10 minutes or a fallback rate above 5%.
- **Runbook:** Ana approves the start and each widening, Marc the move to everyone; a scripted release goes to shadow first, then the canary; a failed deployment leaves the flag on the current version and pages Ana; rollback is the flag above.

Gate:
- [x] Shadow traffic shows the served features and scores match the offline ones
- [x] The rollback was rehearsed and monitors were live before users saw the model
- [x] The online test's decision rule was written before it started, and its result is in

## 7. Live

| Monitor | Layer | Alert when | Owner |
|---|---|---|---|
| p99 latency, fallback rate | System | Over 60 ms, over 5% | Ana |
| Inputs against training, by city | Inputs | PSI above 0.25, missing rate up 5 points, contract violations above 1% | Ana |
| Promise length by city and hour | Outputs | Median moves 3 minutes in a day | Ana |
| On-time rate by city, daily | Outcomes | Below 75% for two days | Marc |
| Monthly retrain job | Pipelines | A failed run, a run twice as long as usual, or a version that fails the gate | Ana |

- **Freshness:** on-time rate falls about 1 point a month as restaurants change; retrained monthly on the latest four months, each version through shadow before it replaces the live one.
- **Retrain gate:** each monthly version trains without the newest 7 days, then must beat the live model and the rule on them; estimates that move more than 5 minutes from the live model's on over 1% of orders stop the release until explained; the quantile is re-checked so that 80% of those orders fall inside the promise. The October version passed on 2026-10-12.
- **The case, live:** checked 2026-09-28 with the online test's effects. Repeat orders +2.1% (about 25,000 orders a month, €63,000 at €2.50 margin) and tickets avoided (about €54,000), against conversion -0.4% (-€12,000; this holds the latency's cost and the longer promises together, so the latency estimate is dropped) and €4,850 of monthly cost: about €100,000 a month net. Next check 2026-12-28, or when the serving bill changes.
- **Incidents:** 2026-10-04: a new city launched with no prep history; promises were the rule's for two weeks as designed; added a monitor for share of fallback estimates by city.

## Log

- 2026-05-26: the request was to rank restaurants with faster deliveries higher in the app. Asked why: late orders drive tickets. The problem is the promise at checkout, so this is a delivery estimate, not a ranking.
- 2026-06-02: framed with Marc; late costs more than early, so the model predicts a quantile. The case breaks even at 1 point of on-time rate and pays back in under a month.
- 2026-06-05: Ana and Marc read `eda.ipynb`; Ana decided to train from March, after the tracking fix of 2026-02-24.
- 2026-06-16: design review passed; online serving with the rule as fallback.
- 2026-07-30: Ana decided the rows, the label and the split in `data.ipynb`, and dropped three post-checkout fields flagged by the leak screen.
- 2026-07-31: Ana wrote the comparison rule and its tie-break, before any fit.
- 2026-08-03: Ana wrote the keep rule, before any feature run.
- 2026-08-12: Deviation: the tuning grid's tree depth widened from 4–8 to 4–10, after the best trial sat at depth 8. Approved by Ana; depth 10 scored within 0.1 of depth 8, so r07 stayed at 8.
- 2026-08-19: Ana chose r07 under the comparison rule; Marc agreed the 80th percentile as the operating point in `eval.ipynb`.
- 2026-08-20: test window used once, on Ana's go; model beats the rule on time by 9 points.
- 2026-08-25: online test design and decision rule written.
- 2026-09-28: P80 shipped to everyone after the online test; the case rechecked with the online effects (about €100,000 a month net); stage set to live.
