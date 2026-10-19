---
name: evaluating-models
description: Decides whether a trained model is better than what the product does today, judged the way the product will use it. Sets the operating point from error costs or capacity (never a default 0.5), compares the model with the rule on the same rows in the decision's unit with intervals, checks every slice that matters, runs error analysis to pick the next fix, and uses the test window once. Use when choosing a threshold or cutoff, comparing a model with a rule or another model, deciding whether a model is good enough or ready, or when a single metric such as accuracy or AUC is offered as the verdict.
---

# Evaluating models

A model is good when the product makes better decisions with it than without it. Evaluation answers that at the operating point the product will use, against the rule it would replace, on every group of users that matters, with the uncertainty stated.

Read `MODEL.md` first: the Decision section has the decision, the costs and the capacity; the Training section has the chosen model and the baselines. If the costs are not there, go back to `framing-models` or state the assumed costs before computing anything.

```
- [ ] 1. Operating point set from costs or capacity
- [ ] 2. Model against the rule, same rows, decision's unit, with an interval
- [ ] 3. Slices checked; losers and too-small slices named
- [ ] 4. Errors analysed; next fix chosen
- [ ] 5. Test window used once
- [ ] 6. MODEL.md Evaluation section and the verdict written
```

## 1. Set the operating point

The threshold is a product decision, made with the costs from the Decision section. Pick the method that matches the decision:

- **Costs per error:** the threshold with the lowest total cost on validation. When the cost of a miss varies by row (the amount of a fraud, the value of an account), the lowest-cost policy acts row by row when the expected cost of acting is lower (act when p × cost of a miss > cost of acting), which needs calibrated scores.
- **Capacity:** the top k per period (40 demos a week); report precision and recall among them.
- **Forecasts:** the quantile the product promises.

```bash
python scripts/threshold.py val_scored.csv --score p --label y --cost-act 40 --cost-fn-col claim_amount --rule-expr "claim_amount > 5000" --time submitted_at
python scripts/threshold.py val_scored.csv --score p --label won --capacity 40 --per week
```

`scripts/` is in this skill's directory: use its full path. Any Python with numpy and pandas runs the scripts; `uv run` installs them if missing. `threshold.py` prints the cost of each policy (the lowest-cost threshold, 0.5, the row-by-row policy, the rule), the range of thresholds that cost about the same, a calibration table, and, with `--time`, the cost of a threshold chosen on the earlier half and applied to the later half. Report the range, not just the point: the owner can pick inside it for workload. Never ship 0.5 because it is the default; it is right only when costs are equal and scores calibrated.

Check the operating point against capacity: a policy that multiplies the review queue is a decision for the threshold owner, not a detail.

## 2. Compare with the rule, in the decision's unit

Score the model and the rule on the same rows, at their operating points, in the unit from the Decision section: euros, deals won per 40 demos, posts wrongly removed per thousand, minutes late. Give a paired interval for the difference.

```bash
python scripts/slices.py test_scored.csv --label y --decision model_flag --baseline rule_flag --by segment country --metric cost --cost-act 40 --cost-fn-col claim_amount
```

`slices.py` resamples the same rows for model and rule, so the interval reflects the comparison, not two separate noises. Threshold-free metrics (AUC, log loss) are for choosing among models; the ship decision is made at the operating point. [reference/metrics.md](reference/metrics.md) lists which metric fits which decision.

## 3. Check the slices

An average hides the users who complain. Slice by what the product cares about: new and returning users, platform, country, plan, price band, entities absent from training, and any group named in the product's fairness commitments. For each slice, report rows, positives, model, rule and the interval of the difference.

- A slice where the model loses to the rule needs its own policy: keep the rule there, a separate threshold, or more data for that group. Do not average it away.
- A slice with fewer than about 30 positives is too small to judge; say so instead of reading its number.
- Check the model's own ranking quality per slice too (AUC or the ranking metric), not only the policy's result. A policy can beat the rule on a slice where the model barely ranks, carried by another signal such as the amount; name such slices as weaknesses to fix.
- With many slices, some will move by chance. Trust a slice result when it is large, when its interval excludes zero, and when it has a plausible cause, such as missing history for new customers.

Fairness checks (demographic parity, equality of opportunity) are in [reference/fairness.md](reference/fairness.md).

## 4. Analyse the errors

1. Sample 50 to 100 errors from validation, both kinds.
2. Tag each with a cause: label noise, missing information, a slice, a feature bug, a genuinely hard case.
3. Count the tags. Prioritize by share of errors times how far that group is from the best achievable (the rule, human agreement, or the label-noise ceiling).
4. Decide whether the fix is data (more examples of a slice, cleaner labels, a new signal) or model. In product work it is usually data (Rules of ML #26, #41).

[reference/error-analysis.md](reference/error-analysis.md) has a worked tagging table.

## 5. Use the test window once

After every choice is made (features, model, threshold), score the test window once and report that number. Record the date and the count in `MODEL.md`. If test results change a choice, the test window has become a validation window: say so, and evaluate on a newer window.

## 6. Verdict

Write the Evaluation section of `MODEL.md` and its gate. The model is ready for `launching-models` when:

- it beats the rule at the operating point on the test window, and the interval of the difference excludes no gain;
- no slice that matters does worse than the rule without its own policy;
- the errors left are listed with their next fix.

Then weigh the gain against what the model costs to build, run and maintain. A gain of a few points in the decision's unit (one more deal a month, two points of precision on a review queue) often does not pay for a model: say so, and recommend shipping the rule first while labels accumulate, or show with numbers why the model is worth it.

Otherwise say which condition fails and what would change it. In the reply, lead with the verdict and the comparison in the decision's unit; then the operating point and who must agree to it, the slices, and the uncertainty. An offline win is a hypothesis about the product; the launch tests it.

## Stop signs

- A verdict resting on accuracy with rare positives, or on AUC alone.
- A threshold of 0.5 that nobody chose.
- A comparison where the model and the rule were scored on different rows or at different operating points.
- A slice with the model behind the rule, averaged away.
- Test numbers that were looked at more than once.
