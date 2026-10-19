# Monitors

## Contents

- Statistics for inputs and outputs
- Thresholds that do not drown you
- Late labels
- Skew, measured in three parts
- What to log

## Statistics for inputs and outputs

| Statistic | For | Reads as |
|---|---|---|
| Missing rate | Every input | A join or upstream source broke. Rules of ML #10: coverage falling from 90% to 60% is a classic failure that raises no error |
| Range checks | Numeric inputs | Values outside the training range: units, encodings, bad defaults |
| Unseen categories | Categorical inputs | A new app version, country or product line the model never saw |
| PSI (population stability index) | Distributions | Under 0.1 stable, 0.1 to 0.25 worth a look, above 0.25 a shift. Bins come from training deciles |
| Kolmogorov-Smirnov | Numeric distributions | With large samples it flags tiny, harmless shifts; read the effect size, not the p-value |
| Mean score and share acted on | Outputs | The first sign that the model sees something different |
| Model age | The deployed version | How long since training, against the freshness curve |

## Thresholds that do not drown you

- Alert on what someone would act on. Every alert has an owner and a first step.
- Compare against the training reference and against the same weekday in recent weeks, so weekly cycles do not alert.
- With many features and segments, some cross any threshold by chance every day. Alert on large effects (PSI above 0.25, missing rate up 5 points), and look at the rest in a daily report.
- Segment the checks that matter most (platform, app version, country): a bug in one segment is diluted in the total.
- Separate the email from the page: problems in a model not yet exported deserve an email; problems in a live model may deserve a page (Rules of ML #9).

## Late labels

When outcomes arrive late (chargebacks, churn at month end, repayment), the newest live period always looks better than it is. Compare outcomes only for periods whose label window has closed, and use inputs and outputs as the early warning in between. Estimate quality on unlabelled data with proxies when the delay is long: agreement with the rule, a labelled audit sample, the share of decisions overturned by people.

## Skew, measured in three parts

Rules of ML #37 splits the gap between training and live performance:

1. **Training against held-out data:** always exists; large means overfitting.
2. **Held-out data against the next day:** large means time-sensitive features or drift.
3. **The next day against live:** should be zero. The same example must score the same in both; any gap is an engineering error in serving.

## What to log

For each prediction: a request id, the time, the model version, the features as served, the score, the decision, and the segment fields (platform, version, country). Join outcomes back by request id when they arrive. This log is the input to every monitor above, the evidence in every diagnosis, and the training data for the next model (Rules of ML #29).
