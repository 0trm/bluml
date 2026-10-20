# Splits

A split is a rehearsal of deployment: the model trains on what it would have known and is tested on what came after. Rules of ML #33: if a model is trained on data until 5 January, test it on data from 6 January on.

## Contents

- Choosing a split
- The gap
- Rolling backtests
- Entity holdouts
- Class balance
- When shuffling is fine

## Choosing a split

| The product | Split |
|---|---|
| Scores known entities again over time (accounts each month, users each visit) | By time: train, then validation, then test, in order |
| Mostly scores entities it has never seen (new restaurants, new items, first-time users) | By time, and also by entity: hold out entities absent from training, and report them separately |
| Has little data and a long history | Rolling backtest (below) instead of one cut |
| Rows truly independent and stationary (rare: a fixed benchmark, lab measurements, a product's category read from its title) | A shuffle is acceptable; write down why |

Keep three parts. Validation is for every choice (features, model, hyperparameters, threshold); test is used once, at the end, to report. When test numbers start steering choices, test has become validation: say so and cut a new test window.

## The gap

When labels look ahead (churn in the next 30 days, fraud reported within 60), the last training rows' labels overlap the start of the test period. Leave a gap at least as long as the label window between the end of training and the start of validation, and again before test.

The newest rows also have labels that are not complete yet (chargebacks still arriving). Leave them out of both training and test until their window has closed, or measure how much the positive rate is still rising.

## Rolling backtests

For small tables or seasonal products, repeat the cut: train up to month t, test on month t + 1, move forward one month, repeat. Report the spread of results across folds, not only their mean. A model that wins on average but loses in the latest folds is losing.

## Entity holdouts

When entities recur across rows (a patient's visits, a customer's months), a random split lets an entity's later rows predict its earlier ones. A time split avoids that, but still lets the model memorize an entity's history. That is right when the product will score that entity again. When it mostly will not, hold out entities: group the split by entity id, so no entity has rows on both sides, and compare results on held-out entities with results on returning ones.

## Class balance

Validation and test keep the real class rate; the operating point and every metric depend on it. For rare positives, reweight or downsample negatives in training only. Downsampling with a known rate keeps calibration recoverable: weight kept negatives by one over the sampling rate (Rules of ML #30), or recalibrate on untouched validation rows.

## When shuffling is fine

The Machine Learning Crash Course shuffles before dividing data, and its own conditions for that are the right test: examples drawn independently and identically, from a distribution that does not change, the same across partitions. Product data rarely meets them. If the positive rate, the feature distributions or the mix of entities change over time, split by time.

The exception that does occur in products is a link between inputs and label that holds over time, such as a product's category read from its title, description or image: there a shuffle and a time split give about the same answer. Check it by running both; if they differ, split by time.
