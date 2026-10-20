# Leaks

A leak is information in a training row that the model will not have when it predicts. It makes offline scores better than live ones, and nothing in the training run reports it. Kaufman et al., *Leakage in Data Mining* (2012), give the formal treatment; this file is the field guide.

## Contents

- The test for every feature
- Leak types, with tells and fixes
- When the screen flags a feature
- Leaks that only show after launch

## The test for every feature

Would this feature exist, with this value, at the moment the prediction is needed? Answer it from the feature's source and the time its value was written, not from its name.

## Leak types

| Type | Example | Tell | Fix |
|---|---|---|---|
| Post-outcome field | `account_closed_date` in a churn model; `cancellation_reason` | Near-perfect single-feature score; missing for one class | Drop it |
| Current-state join | Today's `status` or `plan` joined onto last year's rows | Strength higher on old rows than recent ones | Join the value as of the prediction time (a history or snapshot table) |
| Backfill or recompute | A score backfilled for the months before a system went live; a metric recomputed later over the full history | Strong before the backfill date, weak after; documentation says backfilled or recomputed | Use only values written at the time, or drop the backfilled period |
| Overwritten field | An estimate replaced by the actual value once known: the expected length of a hospital stay overwritten with the real stay | Strong offline, weak live; the column's meaning changed at a date its owner can name | Use the value as first written (a history table, or the log of served features); ask the source's owner when its meaning changed |
| Window past the prediction time | Logins over the month that is being predicted; a rolling rate that includes the current row | Strength drops when the window is shifted back one period | End every window strictly before the prediction time; exclude the row's own outcome |
| Fitted on all rows | A scaler, imputer, category median or target encoding fitted before the split | Validation score falls when fitting moves inside the training fold | Fit on training rows only; target-encode out of fold |
| Duplicates and near-duplicates | The same ticket template, the same user's sessions, resubmitted forms on both sides of the split | Test rows with exact matches in training; score drops on entities never seen | Deduplicate before splitting; hold out by entity when the product scores new ones |
| Identifier leak | Sequential IDs that rise with time; IDs reused from a system that knew the outcome | An ID column with predictive strength | Drop raw IDs; derive only what is known at prediction time (account age) |
| Label proxy | A feature produced by the same process as the label (a reviewer's note in a fraud model trained on that reviewer's verdict) | Feature and label written by the same step | Drop it, or redefine the label |
| Future in the split | Random split over time-ordered rows | Score falls under a time split | Split by time |

## When the screen flags a feature

1. Find where the column comes from: the table, the job that writes it, its documentation.
2. Find when each value is written relative to the prediction time.
3. Compare the feature's strength in old and recent rows, and with and without the latest period.
4. Retrain without it. If the model's score falls to where the other features alone put it, and the feature cannot be shown to exist at prediction time, it stays out.
5. Write the flag, what you found and the decision in the Data section of `MODEL.md`.

A single feature that nearly separates the classes on a behavioural outcome (churn, fraud, clicks) is a leak until proven otherwise. Customers do not announce their decisions in one column.

## Leaks that only show after launch

- **Training-serving skew:** the same feature computed by different code, with different units, defaults or reference tables. Offline scores hold, live ones fall. Rules of ML #29 and #32: log features at serving time, share code.
- **Joined tables that change:** a feature looked up from a table that was updated between training and serving (Rules of ML #31). Snapshot the table, or log what was served.
- **Training rows enriched after the fact:** a reporting job that fills in missing fields (demographics imputed for daily reports) makes training rows fuller than live requests. Log inputs at serving time before and after processing, and compare each one's missing rate with the training rows.
- **An upstream field that changes meaning:** the column keeps its name while its content changes. Watch each feature's correlation with the label as labels arrive: a sudden rise suggests a leak, a slow decline drift.
- **Late labels:** the most recent training rows have positives still missing, so the model learns a lower base rate than the live one.
