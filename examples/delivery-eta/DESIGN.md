# Delivery estimate: design doc

> A worked example: a made-up food delivery startup, written the way `writing-design-docs` asks. Every number is illustrative.

| Status | Author | Reviewers | Decision record |
|---|---|---|---|
| Approved 2026-06-16 | Ana (ML engineer) | Joan (staff engineer, routing), Priya (data platform), Marc (product, checkout) | [MODEL.md](MODEL.md) |

**What this review must decide:** online serving inside checkout's latency budget, or a precomputed table refreshed every five minutes; whether the data platform can log live queue and courier features at serving time from July; and who owns the choice of promised quantile (proposed: Marc, settled by the online test).

## 1. Overview

Customers see "arrives in 25 to 35 minutes" at checkout, computed today from a restaurant's average prep time and distance. It is on time for 71% of orders, and late orders drive most "where is my order" tickets. We propose a gradient-boosted model that predicts the 80th percentile of delivery time from the restaurant's live queue, recent prep times, distance, weather and courier supply, served online at checkout with today's formula as the fallback. We expect on-time orders to rise from 71% to about 80% offline, and the online test to decide whether that raises repeat orders.

## 2. Why, and why now

Late deliveries are the top reason for support tickets (38% of them in Q1) and for one-star ratings. Improving the formula (per-hour prep averages, weather padding) was tried in March: on time rose from 69% to 71% and stalled, because a fixed formula cannot follow a restaurant's queue as it builds. The decision, the cost of each error and the formula's numbers are in [MODEL.md](MODEL.md#1-decision).

## 3. Success criteria

- **Decides the online test:** repeat orders within 30 days, per customer. Tickets avoided already cover the model's monthly cost at 1 point of on-time rate (the case in [MODEL.md](MODEL.md#1-decision)), so the smallest change worth shipping is no loss in repeat orders; four weeks detect a change of 1%.
- **Guardrails:** checkout conversion (no worse than -1%), cancellations, "where is my order" tickets per thousand orders.
- **Operational:** the formula takes over within one request when a feature or the model fails; switching back to the formula is a config change.

## 4. Requirements and constraints

- **Functional:** 95% of checkouts show a model estimate; the promise is the upper end of a 10-minute window; restaurants with under two weeks of history get the formula.
- **Non-functional:** 300 checkouts per second at peak; 60 ms p99 for the estimate within checkout's 250 ms budget; under €2,000 a month to serve.
- **Data and privacy:** no customer personal data in features; addresses are used only as distances, computed by the routing service; logs keep order id, features and estimate for 13 months.
- **In scope:** the estimate at checkout. **Out of scope:** updates after the order is placed (next quarter), courier assignment.
- **Assumptions:** 1,200 restaurants in 4 cities, 40,000 orders a day, growth of 5% a month.

## 5. Methodology

### 5.1 Problem statement

A regression of minutes from checkout to delivery, trained with a quantile (pinball) loss at the promised quantile, because a late order costs more than an early one. The surrogate gap: the model predicts delivery time, while the goal is repeat orders; the promise itself changes order volume and courier load, so only the online test measures the goal.

### 5.2 Data

Orders from March to July (about 5 million), one row per order at checkout. Label: delivery minutes, known within the hour; cancelled orders (4%) have none and are counted separately. Restaurant queue and idle couriers have no history before July: the data platform logs them at serving time from July 1, and until then a daily approximation is used for prototyping only.

### 5.3 Techniques

Baselines first: the formula, then a linear quantile regression on five features. Candidate: gradient-boosted trees with quantile loss. Prep-time medians use only orders delivered before checkout.

### 5.4 Validation and experimentation

Train on March to July, validate on August, test once on September, by checkout time; restaurants that joined after July are reported apart. Offline: pinball loss at 0.8 and the share of orders inside the promise, by city, hour and weather, against the formula. Online: customers randomized into the formula, P70, P80 and P90 for four weeks; success metric repeat orders at 30 days; guardrails as above; decision rule written before start.

### 5.5 Humans in the loop

Operations can pad estimates for a city during an event (a match, a storm) from the admin panel; padded orders are flagged and left out of training.

## 6. Implementation

### 6.1 High-level design

Checkout calls the estimate service with the restaurant, address and time. The service reads the restaurant's queue and prep medians from the feature cache (refreshed every minute), courier supply from the courier service, distance from routing, and returns the window; every request's features and estimate are logged for training.

### 6.2 Serving, scale and performance

Online, because the queue and courier supply change by the minute; a five-minute precomputed table was rejected (see alternatives). Features are cached; the model is about 4 MB and scores in under 5 ms. The service scales horizontally behind checkout's load balancer.

### 6.3 Security and data privacy

Internal service, called only by checkout with service credentials. No personal data stored by this service.

### 6.4 Monitoring and alerts

Inputs by city (ranges, missing rates, drift against training), outputs (promise length by city and hour), outcomes (on-time rate by city, daily), fallback rate and p99 latency. Alerts page the ML on-call.

### 6.5 Cost

From the case in [MODEL.md](MODEL.md#1-decision). Build: 14 engineer weeks, about €35,000. Every month: €1,400 to serve and cache features, sized for 300 checkouts a second at peak; €150 of training compute for a monthly retrain and its search; €600 to log live features; €2,700 of upkeep, a quarter of an engineer; and about €1,200 of checkouts lost to the 20 ms the service adds. Total €6,050 a month, against €48,000 a month of tickets avoided at +8 points on time; repeat orders are upside the online test measures. Break-even is 1 point of on-time rate, and the build pays back in under a month. A five-minute table would avoid most of the latency, but loses the live queue signal the gain comes from (see alternatives).

### 6.6 Integration points

`POST /estimate` with restaurant id, delivery address id and timestamp; returns lower and upper minutes, model version and whether the fallback was used. Upstream owners: data platform (feature cache), routing, courier service. Downstream: checkout and the order tracking page.

### 6.7 Rollout and rollback

Shadow for a week (features and scores compared with offline), 2% canary for two days, then the four-week online test. A config flag selects formula or model version; rollback rehearsed before the canary.

## 7. Risks and uncertainties

- The promise changes demand: shorter promises bring surges that make deliveries later. Watched by the online test's guardrails.
- Queue features exist only from July: the first model trains on six weeks of logged queue data. If that is too little, ship with the daily approximation and retrain monthly.
- New cities have no history: they keep the formula until they have two weeks of orders.

## 8. Alternatives considered

| Alternative | For | Against | Why rejected |
|---|---|---|---|
| Keep the formula, tune it | No new system | Stalled at 71% on time after the March changes | Cannot follow the live queue |
| Predict the mean, add a fixed buffer | Simple loss | The same buffer is too much off-peak and too little at peak | A quantile adapts the buffer to the situation |
| Precomputed table every five minutes | No online dependency in checkout | Queue changes within minutes at peak; 1,200 restaurants × addresses is a large table | Loses the signal that matters most |

## Appendix

- **Offline results (prototype on daily approximations):** on time 79% against the formula's 71%; late by more than 10 minutes 4% against 9%.
- **Milestones:** logging live features from July 1; model ready August 20; shadow August 21; online test from September 1.
- **FAQ from pre-review:** *Why not a separate model per city?* Too little data in smaller cities; city is a feature, and results are reported by city.

## Change log

- 2026-06-09: pre-review with Joan and Priya; switched from a five-minute table to online serving.
- 2026-06-16: approved.
