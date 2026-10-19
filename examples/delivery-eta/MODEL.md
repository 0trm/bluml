# Delivery estimate

Predicts how long an order will take to arrive, to show "arrives in 25 to 35 minutes" at checkout.

> A worked example: a made-up food delivery startup, written the way the bluML skills fill `MODEL.md`. Every number is illustrative.

| Stage | Owner | Threshold owner | Updated |
|---|---|---|---|
| live | Ana (ML engineer) | Marc (product manager, checkout), with operations | 2026-09-28 |

Stages run framing, design, data, training, evaluation, launch, live, retired. Each section ends at a gate; a stage starts only when the gate before it is ticked, with the evidence linked. When work loops back, set the stage back and say why in the log.

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

- **Row:** one order at checkout.
- **Label:** minutes from checkout to delivery. Known within the hour. Missing for cancelled orders (4%), which cluster when things go badly; they are kept as a separate count and checked in every slice.
- **Split:** train March to July, validate August, test September, by checkout time; restaurants that joined after July are reported separately.

| Feature | As of | Source | Note |
|---|---|---|---|
| Restaurant prep time, median of the last 14 days | Checkout, from orders already delivered | orders table | Owner: data platform |
| Open orders at the restaurant | Checkout | live queue service | Logged at serving time |
| Distance by road | Checkout | routing service | Kilometres |
| Idle couriers within 2 km | Checkout | courier service | Logged at serving time |
| Hour, weekday, rain | Checkout | calendar, weather feed | |

- **Leak screen:** `courier_id`, `actual_prep_minutes` and `wait_at_restaurant` dropped: all written after checkout. No other flags.
- **What the product put in the labels:** the promise itself changes behaviour: optimistic promises bring order surges that slow couriers. Measured in the online test, not offline.
- **Label quality:** 200 orders checked against courier GPS; 3 timestamps wrong, from manual completions.

Gate:
- [x] Every feature exists, with this value, at prediction time
- [x] The leak screen ran and every flag is explained
- [x] The split mirrors serving, and training and serving build features with the same code

## 4. Training

| Run | Model | Data version | Validation result | Note |
|---|---|---|---|---|
| r01 | The rule | orders-0731 | pinball@0.8 6.9; on time 71% | Baseline |
| r02 | Linear quantile regression, 5 features | orders-0731 | pinball@0.8 5.6; on time 78% | Simple model |
| r07 | Gradient-boosted trees, quantile loss at 0.8 | orders-0731 | pinball@0.8 4.8; on time 80% | Chosen |

- **Chosen:** r07. It beats the linear model by more than the spread across weekly folds (0.3), and both beat the rule.

Gate:
- [x] Baselines are recorded next to the candidates, on the same validation rows
- [x] Every run can be rebuilt from its record (code, data version, parameters, seed)

## 5. Evaluation

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
- [x] The test window was used once, after every choice was made

## 6. Launch

- **Serving:** online, inside a 60 ms budget; 20 ms added at the median on the serving path; €1,400 a month to serve and cache features. The rule is the fallback when a live feature times out (0.4% of requests in shadow).
- **Input contract:** distance 0 to 25 km, queue 0 to 60 orders, prep median 3 to 90 minutes; violations go to the fallback and are counted.
- **Rollout:** shadow for 7 days (served features and scores matched offline to rounding); canary on 2% for 2 days; online test for 4 weeks; everyone from 2026-09-28.
- **Online test:** arms P70, P80 and P90 against the rule, randomized by customer. Primary metric: repeat orders at 30 days. Guardrails: checkout conversion, cancellations, tickets. Tickets avoided already pay for the model, so the bar for repeat orders is no loss, not a gain. Decision rule written 2026-08-25: ship the arm with the highest repeat rate whose conversion is within 1% of the rule's. Result: P80 shipped (repeat orders +2.1%, interval +0.6 to +3.6; conversion -0.4%).
- **Rollback:** a config flag selects the rule or the model version; rehearsed 2026-08-27; triggered by p99 latency above 60 ms for 10 minutes or a fallback rate above 5%.

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

- **Freshness:** on-time rate falls about 1 point a month as restaurants change; retrained monthly on the latest four months, each version through shadow before it replaces the live one.
- **The case, live:** checked 2026-09-28 with the online test's effects. Repeat orders +2.1% (about 25,000 orders a month, €63,000 at €2.50 margin) and tickets avoided (about €54,000), against conversion -0.4% (-€12,000; this holds the latency's cost and the longer promises together, so the latency estimate is dropped) and €4,850 of monthly cost: about €100,000 a month net. Next check 2026-12-28, or when the serving bill changes.
- **Incidents:** 2026-10-04: a new city launched with no prep history; promises were the rule's for two weeks as designed; added a monitor for share of fallback estimates by city.

## Log

- 2026-06-02: framed with Marc; late costs more than early, so the model predicts a quantile. The case breaks even at 1 point of on-time rate and pays back in under a month.
- 2026-06-16: design review passed; online serving with the rule as fallback.
- 2026-07-30: dropped three post-checkout fields flagged by the leak screen.
- 2026-08-20: test window used once; model beats the rule on time by 9 points.
- 2026-08-25: online test design and decision rule written.
- 2026-09-28: P80 shipped to everyone after the online test; the case rechecked with the online effects (about €100,000 a month net); stage set to live.
