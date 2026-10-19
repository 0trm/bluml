# A diagnosis, worked through

The request: "The returns-abuse model is sending far more returns to manual review since Tuesday. Retrain it on the last month and redeploy."

## 1. Is it real?

Share of returns sent to review, from the decision log rather than the dashboard: 4% for the four weeks before Tuesday 3 March, 11% after. Return volume is steady, so the denominator did not change. No campaign or holiday falls in the window.

## 2. When did it start?

The jump starts on Tuesday 3 March and grows a little each day, the shape of something that accumulates rather than a switch.

## 3. Where is it?

Share sent to review after 3 March, by account age:

| Account created | Sent to review |
|---|---|
| Before 2 March | 4% |
| On or after 2 March | 31% |

All of the increase sits on accounts created since Monday 2 March, and their share of returns grows every day.

## 4. Which layer moved first?

`drift.py` against the training sample, by signup week: `orders_last_90d` and `tenure_days` are missing for every account created since 2 March, and the service fills missing values with 0. The model reads those accounts as brand new with no history, a pattern it learned to associate with abuse. No other input moved. Inputs moved first; scores followed.

## 5. What changed at that moment?

The nightly job that refreshes `customer_history` has failed since a schema migration on the night of 1 March. Accounts that existed before still have their last values; new accounts have none.

## The cause, in one sentence

Since 2 March the `customer_history` job has failed, so new accounts reach the model with no history, the service fills it with zeros, and the model sends their returns to review at about eight times the usual rate.

## The fix

1. Repair the job and backfill the missing days.
2. Make missing history explicit: send it as missing, not zero, and train the model with that case.
3. Add monitors: freshness of `customer_history` (alert when its newest row is more than a day old), and missing rate of each history feature by signup week.
4. Do not retrain on the last month as asked: the model would learn that new accounts with zero history are normal, and the rows from the broken period would teach it nothing true. The model itself is fine on correct inputs; its decisions on older accounts have not changed.

## The incident line in MODEL.md

`2026-03-02 to 2026-03-09: customer_history job failed after a schema migration; new accounts scored with zero history; review share 4% to 11%; detected by the review team after 6 days; fixed by repairing and backfilling the job; added a freshness monitor and a missing-rate check by signup week.`
