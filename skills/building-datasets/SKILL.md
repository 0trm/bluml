---
name: building-datasets
description: Builds the training table for a product model so that every row looks the way the model will see the world when it predicts. Fixes the prediction time, the label, where it comes from and when it becomes known, features as they stood at prediction time, a split that mirrors serving, and the bias the product's own past decisions left in the labels; screens every feature for leaks. Hands the built table to the owner in data.ipynb, where the owner decides the rows, the label and the split. Use when assembling or reviewing training data, choosing a label or a split, when labels are scarce, noisy or must be collected (labelling guidelines, weak supervision, active learning), when a feature or a single column predicts suspiciously well, when labels arrive late or exist only for what the product showed or acted on (clicks on a ranked list, reviewed transactions, approved loans), or when training and serving compute features in different code.
---

# Building datasets

The training table decides what a model can learn and how honest its scores will be. Most product models that disappoint after launch were trained on rows that could not have existed when the prediction was made.

Read the model's `MODEL.md` first; the Decision section says when the model predicts and what the product does with it. If there is no `MODEL.md`, run `framing-models` first, or write down the prediction moment before going on. If nobody has looked at the data yet, run `exploring-data` first: the grain, the window and the outliers it settles are decisions this table inherits.

When the request goes on past the table (train the model, choose its columns, say whether it is ready or worth what it costs), load the skills for those stages now, before going on: `training-models` for the fits and the choice of columns, `evaluating-models` for the verdict, and `doubting-results` for every model number that goes into the reply. Their steps apply once this table is built.

Copy this checklist into your work and tick it as you go:

```
- [ ] 1. Row and prediction time fixed
- [ ] 2. Label defined: its source, when it becomes known, when it stops changing
- [ ] 3. Every feature as of prediction time
- [ ] 4. Leak screen run, every flag explained
- [ ] 5. Split mirrors serving
- [ ] 6. What the product put in the labels, named and handled
- [ ] 7. Training and serving build features with the same code
- [ ] 8. data.ipynb handed over; the owner decided the rows, the label and the split
- [ ] 9. MODEL.md Data section written
```

## 1. Fix the row and the prediction time

One row per entity per moment of prediction: a post at upload, a lead on Monday morning, a claim at submission, a search request. Keep the prediction time as a column. Every join, window and aggregate is relative to it.

## 2. Define the label

- **The event and its window:** what counts as positive, measured over which window after the prediction time ("books a demo within 14 days of the prediction time"). A short window misses part of the outcome (the click, not the purchase); a long one arrives late and is harder to tie to the prediction.
- **When it becomes known, and when it stops changing:** chargebacks arrive weeks late; churn is known at month end; a click within seconds; a purchase counts as a conversion only until the return window closes. Rows whose window has not closed, usually the latest days or weeks, have labels that are still changing. Drop them or mark them, and check whether the positive rate dips at the end of the table.
- **Rows with no outcome:** a cancelled order has no delivery time, a filtered email no user verdict, a rejected loan no repayment. Training only on rows with outcomes teaches a rosier world. Count what is missing and say why.
- **Where it comes from:** user reports, an existing system's records, annotators, or a rule that is right when it fires. Each brings its own bias and delay: users report only what they saw and bothered to flag. With few labels, grow them from a small set checked by hand (weak supervision, active learning, pseudo-labels), and keep a hand-checked set apart for evaluation: a model scored on labels a rule produced is scored on agreeing with that rule. [reference/labels.md](reference/labels.md) covers the sources, guidelines for people who label, and ways to get more labels.
- **Label quality:** read 50 to 100 labels against their rows. Labels that contradict an obvious signal (a five-star review labelled as a complaint) are noise or a second process; estimate their share, since it caps any model's accuracy. When people label, give them a written guideline and measure how often two of them agree on the same items before trusting the labels.

## 3. Build features as of prediction time

For each feature, write down the moment its value was known. The test for every column: would it exist, with this value, at the moment the prediction is needed? Typical failures:

- Tables that hold current state (status, latest score, `updated_at`) joined onto old rows.
- Columns backfilled or recomputed after the fact, for example when a system went live or a metric was redefined.
- Windows that end after the prediction time or include the row's own outcome, such as a rolling click rate that counts the click being predicted.
- Encoders, scalers, imputers or category medians fitted on all rows, test rows included.
- Identifiers that encode time or the outcome.

[reference/leaks.md](reference/leaks.md) lists the leak types with their tells and fixes.

## 4. Screen for leaks

Run the screen on the table before training anything:

```bash
python scripts/leakage_screen.py data.csv --label booked_demo --time scored_at
```

`scripts/` is in this skill's directory: use its full path. Any Python with numpy and pandas runs it; `uv run` installs them if missing. It reports each feature's strength on its own, overall and in consecutive stretches of time, and flags features that are too strong, change strength over time, go missing for one class, or behave like identifiers, plus split overlaps and duplicates when given `--split`.

Treat every flag as a leak until the feature's source and timestamp explain it. A feature that alone scores an AUC above 0.9 on a behavioural outcome is excluded until proven innocent; a feature that is strong in old rows and weak in recent ones was produced differently over time and will fail in production. Write each flag and its explanation in `MODEL.md`.

## 5. Split like serving

- **Time-ordered rows (almost every product table):** train on the past, validate on the next window, test on the latest window. Leave a gap as long as the label window so training labels never overlap the test period.
- **The product will score entities it has never seen** (new users, new items, new restaurants): also hold out whole entities, and report results on them separately.
- **Shuffle only** when rows are independent and the link between inputs and label does not change over time, such as a product's category read from its title. Say why that holds if you do it.
- Keep the real class rate in validation and test. Reweight or resample only the training rows, and only when the model fails to learn the minority class; recalibrate afterwards.
- Once the split column exists, run the screen again with it and the entity column, `--split split --id lead_id`, to check splits that overlap in time, entities in more than one split and rows duplicated across splits.

[reference/splits.md](reference/splits.md) covers gaps, rolling backtests and entity holdouts.

## 6. Name what the product put in the labels

The product's past decisions decide which rows have labels and what they say:

- **Position and exposure:** a click on a ranked list measures position as much as appeal, and an item never shown cannot be clicked. Ranking by past clicks keeps new items low forever.
- **Selection:** outcomes exist only for what the product acted on: reviewed payments, approved loans, called accounts, and sales capped by the stock the last forecast ordered.
- **Interventions:** once a model drives action, the label changes meaning: an account that was called and stayed may have been saved.

Look for randomised traffic first (a random-order holdout, an exploration slice, a control group): it is the only unbiased evidence in the table. Then correct: position as a feature held fixed at scoring time, inverse propensity weights estimated from the random traffic, or training and evaluating on the random slice. If no random traffic exists, say the offline numbers favour the current system and plan to collect some. [reference/product-bias.md](reference/product-bias.md) has the methods.

## 7. Share feature code between training and serving

Training and serving must compute each feature the same way: same units, windows, defaults for missing values, category maps and reference tables. The safest route is to log features at serving time and train on the log. Otherwise use one function for both, and write a parity check: the same entity at the same moment gets the same values from both paths. Compare missing rates too: a training table enriched upstream (fields filled in for reports) is fuller than what serving will see.

## 8. Hand the table to the owner

The model's owner decides the rows, the label and the split; the agent prepares the evidence. Copy [templates/data.ipynb](templates/data.ipynb) to `data.ipynb` beside `MODEL.md` and fill its header and setup from the steps above. It follows the layout of `eda.ipynb` (`exploring-data` steps 2 and 4) and has three sections on the built table:

1. **The label, the rows and the split:** the label rate over prediction time, with the split boundaries and the rows whose window is still open marked, and rows, positives and rate per split. The decision: the rows, the label window and the split.
2. **Each feature by origin and split:** the features grouped by where their value comes from, with each one's missing rate and quartiles per split, so a feature that looks different in test than in training shows before any model sees it.
3. **The leak screen as a chart:** each feature's strength alone, against the too-strong line, and the flagged features across the stretches of time, from `scripts/leakage_screen.py`. The decision: which flagged features stay out.

Write each question, its options and the rule for choosing before drawing the charts, and the agent's reading folded, ending with its recommendation where there is a decision. Run it end to end (`jupyter nbconvert --to notebook --execute --inplace data.ipynb`) and hand it over with `jupyter lab data.ipynb`; in chat, give no reading or recommendation until the owner has written their pick. The owner writes a reading and a pick, opens the folded reading, then writes the decision in their own words. Read the notes back as `exploring-data` step 5 does, copy each decision into `MODEL.md` with the date, and start training only when the owner says go.

A row definition, a label window or a split changed after a model's result was seen is a deviation: stop, and write it in the `MODEL.md` log with what changed, from what to what, and the result that prompted it.

Working alone (the request says nobody can answer until the work is done), skip the notebook and the waiting: take each decision on the agent's pick, add it to the `MODEL.md` log as an open decision with its options and evidence, and list the open decisions in the reply.

## 9. Write it down

Fill the Data section of `MODEL.md`: the path to `data.ipynb` and the decisions taken there, the row, the label and its delay, the feature table with each as-of time, the split, the leak screen's result and what was dropped, what the product put in the labels, and where the labels come from and how good they are. Mark each gate item whose evidence is in place with `(holds: {evidence})`; only the owner ticks it. Set the stage to training once the owner has ticked the gate and said go, and log the date. Training starts with `training-models`.

## Stop signs

- A feature that alone nearly predicts the label.
- A label that is only known for rows the current system acted on, with no random slice to correct it.
- A random split over time-ordered rows, or the same entities on both sides when the product scores new ones.
- Rows, a label or a split the owner never picked, or one changed after a model's result was seen with no deviation in the log.
- Feature code for serving that differs from the training code.
- A column documented as backfilled, recomputed, latest or current.
- Evaluation labels written by a rule or a model, with no set checked by hand.
