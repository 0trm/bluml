# Metrics for decisions

Pick the metric from the decision, then report it at the operating point the product will use.

## Contents

- Which metric for which decision
- Threshold-free metrics, and their place
- Ranking
- Forecasts
- Calibration
- Uncertainty

## Which metric for which decision

| Decision | Report | Avoid as the verdict |
|---|---|---|
| Act or not, with known costs (claims investigation, spam filtering) | Total cost in money at the operating point; precision, recall and flag rate there | Accuracy; AUC alone; F1, which weighs both errors equally |
| Act on a fixed number (40 demos a week) | Hits, precision and recall in the top k per period; lift over random k | Any metric over all rows |
| Route between two queues | Items routed wrongly per thousand, in each direction, weighted by what each costs | Accuracy, unless both directions cost the same |
| Order a list | A ranking metric on the top slots (NDCG@k, recall@k, clicks per visit), corrected for position; then an online test | Offline metrics on logs the current ranker produced |
| Promise a number (delivery time) | Pinball loss at the promised quantile; share of outcomes inside the promise, by slice | Mean squared error, when lateness costs more than earliness |
| Estimate an amount (demand, value) | Mean absolute error in the product's unit, and bias (mean error) | R² on its own |

With rare positives, accuracy rewards predicting the majority: 97% accuracy is what "never" scores when 3% are positive.

## Threshold-free metrics, and their place

AUC and log loss compare models across all thresholds. Use them to choose among candidates and to watch training. The decision to ship is made at the one threshold the product will use, where two models with the same AUC can differ widely. Rules of ML #9 gates export on a held-out AUC; that is a sanity check before export, not the launch decision.

## Ranking

Logged clicks reflect the order that produced them. Evaluate rankings on random-order traffic, with position-debiased labels, or with a counterfactual estimate (see `building-datasets`, reference/product-bias.md), and treat the result as a hypothesis for an online test.

## Forecasts

When late and early cost differently, the product promises a quantile, and the model should be trained and judged at it. Report calibration of the quantile: a promise at the 80th percentile should be met about 80% of the time, overall and in each slice (rain, peak hours, new restaurants).

## Calibration

A score used as a probability (cost thresholds, expected value, a displayed percentage) must match observed rates. Check a reliability table on validation: rows binned by score, mean score against observed rate. Prediction bias (the mean score against the base rate) is the quickest check. Recalibrate on rows the model did not train on, and check again on rows the calibration did not see.

## Uncertainty

- Give an interval for every comparison: a paired bootstrap over rows (the same rows resampled for both models) or over entities when rows from one entity are correlated.
- Count positives, not rows: 60,000 transactions with 30 frauds in a slice is a slice of 30.
- With many slices or metrics, some differences appear by chance. Prefer few, pre-chosen slices; treat surprising slice results as hypotheses to confirm on new data.
