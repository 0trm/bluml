---
name: training-models
description: Trains a product model the way a production ML engineer would. Baselines first, then the simplest model that can beat them, debugged before tuned, tuned on validation rows only, with every run recorded so it can be rebuilt. Use when fitting, comparing or tuning models, choosing an algorithm, when a loss will not settle or a model will not beat a simple baseline, when deciding whether more data or more tuning will help, when a training result looks too good, or before reporting any model as the best one.
---

# Training models

Training is the step people expect to take the most time, and in product work it should take the least. Its job is to find the simplest model that beats the rule by enough to be worth running, on rows that rehearse deployment.

Read `MODEL.md` first. Training needs the Decision section (the decision, the operating point and the rule's number) and the Data section (the split and the features cleared by the leak screen). If the Data gate is not ticked, go back to `building-datasets`: a model trained on an unscreened table only measures its leaks.

## 1. Baselines first, on the validation rows

Score these before any real model, on the same validation rows, at the operating point from the Decision section (a cost-based threshold, the top k, a quantile), and record each one:

- **The trivial baseline:** the majority class, the base rate, the last value, or random at the same capacity.
- **The rule:** today's rule or system, or the simple rule written in framing.
- **A simple model:** logistic or linear regression on a handful of well-understood features.

The simple model also tests the pipeline: if it cannot beat the trivial baseline, the label, the features or the join are broken. Fix that before trying anything bigger.

## 2. The simplest model that can win

- **Tabular data:** gradient-boosted trees. They handle mixed types, missing values and interactions with little tuning.
- **Small data, or a model people must read:** a regularized linear model; it is also easier to calibrate and debug (Rules of ML #14).
- **Text, images, audio:** start from pretrained embeddings or a pretrained model; train a deep network from scratch only with a great deal of data.
- **Forecasts with asymmetric costs:** a quantile loss at the quantile the product will promise, not squared error.
- **Many classes, some rare:** one binary classifier per class tends to beat a single multi-class model and is easier to calibrate, and a new class is one more model rather than a retrain. The cost is more models to run and monitor.
- **Rows from segments that differ in kind** (stores, regions, clinics): compare one model per segment with one pooled model on the same validation rows. Neither wins by default.

Add complexity only when it beats the simpler model by more than the difference between validation folds. A model that is better by noise is worse in production, because it costs more to run and explain. Complex work looks like more effort and earns more credit; neither is a reason to ship it.

## 3. Debug before tuning

1. **Overfit a tiny sample.** A model that cannot drive the training loss near zero on 100 rows has a bug in the data, the labels or the code.
2. **Fix the seed** and confirm two runs give the same result.
3. **Plot training and validation loss** by iteration or epoch. Validation rising while training falls is overfitting; validation better than training is a leak, a split error or regularization that only applies in training.
4. **Look at the predictions:** their distribution (a single repeated score is a bug), the mean prediction against the actual rate (a gap is prediction bias), and the most important features (one dominant feature is a leak until the leak screen says otherwise).

[reference/debugging.md](reference/debugging.md) has the symptoms and their usual causes.

## 4. Tune on validation only

- Tune on the validation window, or with rolling time-ordered folds; never on test.
- Before a long search, find the ceiling. Let the model overfit and score it on its own training rows: if even that does not beat the rule by the break-even gain, these features cannot get there, and the fix is new signal or a new framing, not tuning (a high score here proves little). Then train on a quarter, half and all of the rows and score each on the same validation rows: a curve still rising means more data will help; a flat one means it won't.
- Search a few parameters that matter (tree depth, learning rate, number of trees, regularization) over a small grid or random search, not everything.
- Keep every trial: parameters, validation result at the operating point, seed.
- Stop when the best trials differ by less than the variation between folds or seeds.

## 5. Calibrate when the decision uses the probability

If the Decision section sets the threshold from costs, or the product multiplies the score by an amount, the score must read as a probability. Check a reliability table on validation (mean score against the observed rate by score bin). If they differ, calibrate on validation rows (isotonic or Platt scaling) and check again on rows the calibration did not see. Resampled or reweighted training data always needs this step.

## 6. Record every run

A run is reproducible when its record names the code version, the data version (a hash or snapshot id of the training table, and the period it covers), the parameters, the seed, the operating point (the threshold or k), the validation result there, and where the model file is. Use the team's tracker (MLflow, Weights & Biases, a CSV) and put the run id in `MODEL.md`. A number from a run nobody can rebuild is not evidence. Metrics computed on training data, such as some autologged ones, describe the fit, not the model's quality. [reference/run-records.md](reference/run-records.md) shows a minimal record and the MLflow version of it.

## 7. Choose

Pick the simplest model within noise of the best one, and confirm it beats the rule at the operating point on validation by more than it costs to build, serve and maintain. Write the comparison table and the ceiling in the Training section of `MODEL.md` (baselines and candidates, same rows, same unit), tick the gate items that hold, set the stage to evaluation, and hand over to `evaluating-models`. Do not touch the test window here.

Before the handover, ask a colleague to review the method the way code is reviewed: any feature that will not exist at prediction time, a split that lets the future in, and the ceiling. These mistakes stay hidden until late unless someone else looks. `doubting-results` lists the checks.

## Stop signs

- Validation far above the rule or above what similar products achieve: run `doubting-results` before going further.
- No model beats the trivial baseline: the data holds little signal for this label; go back to `framing-models`.
- The best model beats the simple one by less than the noise between folds.
- A result that cannot be rebuilt from its record.
