# Monitors

## Contents

- Statistics for inputs and outputs
- Thresholds that do not drown you
- Late labels
- Output audits
- Skew, measured in three parts
- What to log

## Statistics for inputs and outputs

| Statistic | For | Reads as |
|---|---|---|
| Row count | Every table and batch | A partial or doubled load, or a source that stopped sending; compare with the same weekday in recent weeks |
| Duplicate keys | Keys used in joins | A key that is no longer unique multiplies rows in every join |
| Missing rate | Every input | A join or upstream source broke. Rules of ML #10: coverage falling from 90% to 60% is a classic failure that raises no error |
| Range checks | Numeric inputs | Values outside the training range: units, encodings, bad defaults |
| Formats | Dates and other parsed fields | A date that switches from day-month to month-day still parses, and lands in the wrong month |
| Unseen categories | Categorical inputs | A new app version, country or product line the model never saw; or a value renamed or recased upstream (`male` to `Male`), which the encoder reads as missing without any error |
| PSI (population stability index) | Distributions | Under 0.1 stable, 0.1 to 0.25 worth a look, above 0.25 a shift. Bins come from training deciles |
| Kolmogorov-Smirnov | Numeric distributions | With large samples it flags tiny, harmless shifts; read the effect size, not the p-value |
| Correlation with the label | Each feature, as labels arrive | A sudden rise suggests a leak; a slow decline, drift |
| Mean score and share acted on | Outputs | The first sign that the model sees something different |
| Feature importance | Each retrained version | A feature that jumps in importance may be leaking |
| Outcomes by group | Groups named in the fairness check (`evaluating-models`) | A gap opening between groups after launch |
| Overrides | Decisions people can change | A rising share means people do not trust the model and work around it; the product metric pays for it |
| Model age | The deployed version | How long since training, against the freshness curve |

## Thresholds that do not drown you

- Alert on what someone would act on. Every alert has an owner and a first step. A team that gets too many alerts stops reading them, so page only for what is likely to be real and costly to miss, such as anything customers see.
- Compare against the training reference and against the same weekday in recent weeks, so weekly cycles do not alert.
- With many features and segments, some cross any threshold by chance every day. Alert on large effects (PSI above 0.25, missing rate up 5 points), and look at the rest in a daily report.
- Segment the checks that matter most (platform, app version, country): a bug in one segment is diluted in the total.
- Separate the email from the page: problems in a model not yet exported deserve an email; problems in a live model may deserve a page (Rules of ML #9).

## Late labels

When outcomes arrive late (chargebacks, churn at month end, repayment), the newest live period always looks better than it is. Compare outcomes only for periods whose label window has closed, and use inputs and outputs as the early warning in between. Estimate quality on unlabelled data with proxies when the delay is long: agreement with the rule, a labelled audit sample, the share of decisions overturned by people.

## Output audits

When outputs feed the next training set (flags that become labels, items the model chose to show), errors compound: a classifier trained on yesterday's flags learns yesterday's mistakes. Every week or month, have people review a small random sample of outputs, 1 to 5%. Count the errors by kind, look for patterns the model has not seen (a new kind of fraud), fix what a rule can fix now, and send the rest to be relabelled. Record each review in the Live section of `MODEL.md`, as a monitor with an owner.

## Skew, measured in three parts

Rules of ML #37 splits the gap between training and live performance:

1. **Training against held-out data:** always exists; large means overfitting.
2. **Held-out data against the next day:** large means time-sensitive features or drift.
3. **The next day against live:** should be zero. The same example must score the same in both; any gap is an engineering error in serving.

## What to log

For each prediction: a request id, the time, the model version, the features as served, the score, the decision, and the segment fields (platform, version, country). Join outcomes back by request id when they arrive. This log is the input to every monitor above, the evidence in every diagnosis, and the training data for the next model (Rules of ML #29).
