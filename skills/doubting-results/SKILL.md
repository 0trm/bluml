---
name: doubting-results
description: Checks a model result before it is reported, compared or acted on. Catches scores too good to be true, leaked features, shuffled time splits, a test set used more than once, metrics computed on training data, comparisons on different rows or at different thresholds, accuracy on rare positives, missing intervals, slices too small to judge, and labels written by a rule or by the model itself. Use before writing any model metric into an answer, a MODEL.md, a launch plan or a report; whenever a result beats expectations; and whenever someone else's offline number is offered as the reason to ship or to retrain.
---

# Doubting results

A good number is a claim, and in product ML the claims that fail are the ones nobody checked: the code ran, the metric printed, and the error that made it wrong raised no exception. Before a model number leaves your hands, run these checks. Each takes minutes; the failures they catch take weeks to find after launch.

## The checks

1. **Too good to be true?** Behavioural outcomes (churn, fraud, clicks, conversion) are hard to predict. An AUC above about 0.9, a single feature that nearly separates the classes, or a large jump in week one is a leak until shown otherwise. Run the leak screen in `building-datasets`, retrain without the strongest feature, and check whether its strength holds in recent rows.

2. **Rows the model could not have seen?** Was the split by time for time-ordered rows? Do the same entities, duplicates or templates appear on both sides when the product will mostly score new ones? Were scalers, encoders or medians fitted before the split?

3. **Which data produced the number?** Training data (autologged training metrics, in-sample fit) says nothing about quality. Validation used for tuning is optimistic. Test used more than once, or used to choose among models, is validation. Say which one the number comes from.

4. **The right comparison?** The model and the baseline must be scored on the same rows, at their operating points, in the decision's unit. A model compared with nothing, or with a baseline scored on other rows or another period, has no result. Compare with the rule the product uses today, not only with a weaker model.

5. **The product's operating point?** Accuracy with rare positives rewards predicting "never". AUC and log loss compare models; the product acts at one threshold, a capacity or a quantile. Report the number there.

6. **How sure?** Give an interval for the difference that matters (a paired bootstrap over rows or entities). Count positives, not rows. A slice with a few dozen positives cannot carry a conclusion; with many slices, some move by chance.

7. **Does the data mean what the code assumes?** Read ten raw rows. Check units, codes that read as missing values (a literal "NA" or "None" parsed as null), labels still maturing in the latest period, and rows that exist only because the old system acted on them.

8. **Will it hold live?** Is each feature computed the same way in serving? Do the logged clicks or outcomes reflect what the current system chose to show? An offline result on logs the current system produced favours the current system. Have the team's past offline gains held up in online tests? If nobody has checked, or they have not, an offline win is weak evidence.

9. **Who wrote the labels?** Labels written by a rule or a model (weak labels, pseudo-labels, a filter's past verdicts) agree with whatever wrote them. Scored on them, that rule looks perfect, and a model looks good for copying it. Evaluate on labels people checked.

## Report the checks

Put a short block next to any model number you report:

```
Checks: leak screen clean (top single-feature AUC 0.71); time split, test April to June, used
once; compared with the stage rule on the same quarter at 40 demos a week; 95% interval of the
difference +1.1 to +4.0 won deals a month; June deals may still be open.
```

When a check fails, say so first, before the number, and say what it changes: "The 0.97 AUC comes from `last_stage_reached`, which the CRM overwrites when a deal closes; without it the model scores 0.74 on the latest quarter."

When a number will decide a launch, have a colleague review the method the way code is reviewed, with these checks in hand: features that will not exist at prediction time, the split, and the ceiling the training rows put on the result. The author is the person least likely to see their own leak.

## When the number is someone else's

The same checks apply to an evaluation you are handed: a launch request that cites "+2 AUC points", a dashboard, a vendor's benchmark. Read the code or the method behind it before planning around it. A launch plan built on an unchecked number ships whatever was wrong with it.
