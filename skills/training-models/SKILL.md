---
name: training-models
description: Trains a product model the way a production ML engineer would, with the model's owner deciding at every step. A card for each candidate and the comparison rule come before any fit; then baselines, debugging and the ceiling, feature groups kept by a rule the owner writes before any run, tuning on validation rows only, and the choice. Each step ends in train.ipynb with a chart, the owner's reading and pick, the agent's folded reading and recommendation, and the owner's decision, and the next step starts only on the owner's go. Every run is recorded with its charts so it can be rebuilt. Use when fitting, comparing or tuning models, choosing an algorithm, choosing which features or predictors to keep, when a loss will not settle or a model will not beat a simple baseline, when deciding whether more data or more tuning will help, when a training result looks too good, or before reporting any model as the best one.
---

# Training models

Training is the step people expect to take the most time, and in product work it should take the least. Its job is to find the simplest model that beats the rule by enough to be worth running, on rows that rehearse deployment.

Load `doubting-results` now, before the first query on the data: every model number in the reply goes through its checks first. Load `evaluating-models` now as well, unless the request is only about the fit itself (a loss that will not settle, a tuning run): a model built for use ends in its verdict on whether it beats the rule at the operating point, and so does a request to choose the columns or to say whether a feature or its data source is worth what it costs. Training's steps still come first, and each skill's steps apply when its stage starts.

Read `MODEL.md` first. Training needs the Decision section (the decision, the operating point and the rule's number) and the Data section (the split and the features cleared by the leak screen). If the Data gate is not ticked, or, working alone, has an item that does not hold, go back to `building-datasets`: a model trained on an unscreened table only measures its leaks.

## How each step ends

The model's owner takes every decision below; the agent prepares it. Each numbered step ends at a stop:

1. Before running anything, write the step's question, its options and the rule for choosing in its section of `train.ipynb`.
2. Run the step, draw its charts, log its runs, and write the agent's reading, folded, ending with its recommendation.
3. Hand the notebook over. In chat, name the step, its question and options, the routine work done since the last stop, and how to open it (`jupyter lab train.ipynb`); give no reading or recommendation there until the owner has written their pick.
4. The owner looks first, writes a reading and a pick, opens the folded reading, then writes the decision in their own words. Copy it into `MODEL.md` with the date.
5. Start the next step only when the owner says go: one step per turn.

Routine work between stops (a rebuild, a bug fix, a pinned version) runs without one. A rule, a design decision or a setting changed after its result was seen (a keep rule loosened, a tie-break swapped, a grid widened because the best trial sat at its edge) is a deviation: stop, and write it in the `MODEL.md` log with what changed, from what to what, and the result that prompted it. The owner approves it or the old rule stands.

**Working alone** (the request says nobody can answer until the work is done): skip the notebook and the waiting, and go through every step. At each stop, add an open decision to the `MODEL.md` log (the question, the options, the rule, and the agent's pick with its evidence), go on with that pick, and list the open decisions in the reply for the owner to take. Write the comparison rule (step 1) and the keep rule (step 4) yourself, before the runs they judge, and say so in the reply.

## The notebook

Copy [templates/train.ipynb](templates/train.ipynb) to `train.ipynb` beside `MODEL.md` and fill its header from `MODEL.md`. It has one section per step below, in the layout of `eda.ipynb` (`exploring-data` steps 2 and 4): a question with the decision's options and rule, a chart or a table, the owner's box, the agent's folded reading and recommendation, and the owner's decision. Keep its tags and folding. Fill a section when its step starts; the later ones stay as the template left them.

Run it end to end after each step, so the saved charts are the ones the owner reads:

```bash
jupyter nbconvert --to notebook --execute --inplace train.ipynb
```

A section whose fits are slow saves its results the first time and reads them back on later runs. Outputs show counts and charts, never rows or row-level identifiers. Read the owner's notes back as `exploring-data` step 5 does: a box with the placeholder has no reading, and a folded reading saved open above an empty box was read first.

## 1. Write a card for each candidate, before any fit

Name the baselines every candidate must beat (step 2), then one card per candidate model: what it assumes about the data, what it costs to serve (latency, compute, upkeep), and how it fails first. Choose the candidates from these:

- **Tabular data:** gradient-boosted trees. They handle mixed types, missing values and interactions with little tuning.
- **Small data, or a model people must read:** a regularized linear model; it is also easier to calibrate and debug (Rules of ML #14).
- **Text, images, audio:** start from pretrained embeddings or a pretrained model; train a deep network from scratch only with a great deal of data.
- **Forecasts with asymmetric costs:** a quantile loss at the quantile the product will promise, not squared error.
- **Many classes, some rare:** one binary classifier per class tends to beat a single multi-class model and is easier to calibrate, and a new class is one more model rather than a retrain. The cost is more models to run and monitor.
- **Rows from segments that differ in kind** (stores, regions, clinics): one model per segment against one pooled model on the same validation rows. Neither wins by default.

The stop: the owner writes the comparison rule and its tie-break before any result exists, for example "the best won deals at 40 a week wins when it beats the next by more than the spread between folds; the simpler model wins a tie". Complexity earns its place only by beating the simpler model by more than the difference between validation folds. A model that is better by noise is worse in production, because it costs more to run and explain. Complex work looks like more effort and earns more credit; neither is a reason to ship it.

## 2. Baselines first, on the validation rows

Score these before any real model, on the same validation rows, at the operating point from the Decision section (a cost-based threshold, the top k, a quantile), and record each one:

- **The trivial baseline:** the majority class, the base rate, the last value, or random at the same capacity.
- **The rule:** today's rule or system, or the simple rule written in framing.
- **A simple model:** logistic or linear regression on a handful of well-understood features.

The simple model also tests the pipeline: if it cannot beat the trivial baseline, the label, the features or the join are broken. The stop: a chart of each baseline with the spread between folds, and the owner's call to fit the candidates or fix the pipeline first.

## 3. Debug, then find the ceiling

1. **Overfit a tiny sample.** A model that cannot drive the training loss near zero on 100 rows has a bug in the data, the labels or the code.
2. **Fix the seed** and confirm two runs give the same result.
3. **Plot training and validation loss** by iteration or epoch. Validation rising while training falls is overfitting; validation better than training is a leak, a split error or regularization that only applies in training.
4. **Look at the predictions:** their distribution (a single repeated score is a bug), the mean prediction against the actual rate (a gap is prediction bias), and the most important features (one dominant feature is a leak until the leak screen says otherwise).
5. **Find the ceiling.** Let the model overfit and score it on its own training rows: if even that does not beat the rule by the break-even gain, these features cannot get there, and the fix is new signal or a new framing, not tuning (a high score here proves little). A new framing can be a smaller question: a regression that cannot predict the value closely enough may only need to say whether it lands above a threshold. Then train on a quarter, half and all of the rows and score each on the same validation rows: a curve still rising means more data will help; a flat one means it won't.

[reference/debugging.md](reference/debugging.md) has the symptoms and their usual causes. The stop: the loss curves, the ceiling against the rule plus the break-even gain, and the learning curve, and the owner's call to go on, find new signal, or get more data.

## 4. Choose the features

Every feature served is a pipeline to run, a parity check, a monitor and one more way to fail, so it stays only if it earns its place on the validation rows. Start from the features the leak screen cleared.

**Before any run, the keep rule.** Group the features by meaning (account history, recent activity, price), say why each group is worth trying, and write two or three keep rules to choose from: for example, keep a group whose gain at the operating point beats the spread between folds, or one whose gain is twice that spread and pays its upkeep. The stop: the owner writes the keep rule. Every run below is judged by it.

Then run the comparisons:

1. **Start with a handful:** the simple model's features, fields observed directly and understood by the people who own them (Rules of ML #17). Keep the count in proportion to the rows: about a dozen features for a thousand rows in a linear model (#21).
2. **Add one group at a time.** Keep a group only when it passes the keep rule. Run these comparisons, and the ablation in point 4, with a model that can combine features, such as the boosted trees from step 1. A linear model weighs each feature on its own, so a feature that matters only next to another adds nothing there: a promo-code flag that lifts conversion on first visits and lowers it on returning ones can cancel out to no gain. When the chosen model is linear, cross such a feature with the one it depends on (Rules of ML #20), and keep the cross only if it earns its place. Each comparison is a recorded run.
3. **Drop near-duplicates.** Two features that carry the same information (the same quantity in two units, a count and its log, a rank correlation above about 0.9) split the importance between them and double the upkeep. Keep the one that is cheaper to serve and easier to explain.
4. **Ablate the final set.** Groups interact, so retrain once without each group on the same rows. A group whose removal costs less than the noise between folds goes: an unused feature is debt (#22).

**After the runs, the stop:** a gain chart for each measure (each group's gain against the spread between folds), the ablation chart, and a heatmap of rank correlations with the near-duplicate pairs marked. The agent's folded reading proposes the kept groups, each dropped near-duplicate beside the column it repeats and the one that stayed, and a draft Why in line per kept feature. The owner picks the groups and writes each Why in line in the feature table of `MODEL.md`: the baseline, or the gain its group added and the run that showed it. A feature with no line there is not served. Working alone, the agent writes the lines and marks them open.

When the request asks which features the model needs, the reply gives the same reasons with their numbers: what removing each kept group costs, from the ablation in point 4, and for a column weak on its own, what removing that column costs or the rate that shows the interaction. "Strong in combination" without its number is not evidence. Name the dropped columns in the reply too, by reason: each near-duplicate beside the column it repeats and which of the two stayed, then the ones that added nothing. "The duplicates" or "everything else" without their names leaves the owner guessing which columns to retire.

Do not choose by each feature's score alone (its correlation or mutual information with the label, the leak screen's AUC): a feature weak alone can matter next to others, and one strong alone is a leak until the screen explains it. L1 regularization and tree importance can propose drops; confirm each with a run, as in point 4. `monitoring-models` repeats the check on the newest rows every quarter.

## 5. Tune on validation only

- Tune on the validation window, or with rolling time-ordered folds; never on test.
- Search a few parameters that matter (tree depth, learning rate, number of trees, regularization) over a small grid or random search, not everything. Write the grid before the search: widening it after the best trial lands at an edge is a deviation.
- Keep every trial: parameters, validation result at the operating point, seed.
- Stop when the best trials differ by less than the variation between folds or seeds.

The stop: each trial's result against the settings searched, with the spread between folds, and the owner's call on the trial to keep or to stop tuning.

## 6. Calibrate when the decision uses the probability

If the Decision section sets the threshold from costs, or the product multiplies the score by an amount, the score must read as a probability. Check a reliability table on validation (mean score against the observed rate by score bin). If they differ, calibrate on validation rows (isotonic or Platt scaling) and check again on rows the calibration did not see. Resampled or reweighted training data always needs this step. The reliability chart goes into the choice in step 8.

## 7. Record every run

A run is reproducible when its record names the code version, the data version (a hash or snapshot id of the training table, and the period it covers), the parameters, the seed, the operating point (the threshold or k), the validation result there, and where the model file is. Use the team's tracker (MLflow, Weights & Biases, a CSV) and put the run id in `MODEL.md`. In MLflow, tag every run with its step (`mlflow.set_tag("step", "features")`) and log every chart the notebook draws from it (`mlflow.log_figure`), so the runs page shows each run's evidence; the notebook's setup cell has a `log_charts` helper that does both. A number from a run nobody can rebuild is not evidence. Metrics computed on training data, such as some autologged ones, describe the fit, not the model's quality. [reference/run-records.md](reference/run-records.md) shows a minimal record and the MLflow version of it.

## 8. Choose

The stop: every baseline and candidate at the operating point on the same validation rows, with the spread between folds, the rule and the break-even line, and the reliability chart when step 6 applies. The owner picks by the comparison rule from step 1: the simplest model within noise of the best one, confirmed to beat the rule at the operating point on validation by more than it costs to build, serve and maintain.

Write the comparison table and the ceiling in the Training section of `MODEL.md` (baselines and candidates, same rows, same unit). Mark each gate item whose evidence is in place with `(holds: {evidence})`; only the owner ticks it. Set the stage to evaluation once the owner has ticked the gate and said go, and hand over to `evaluating-models`. Do not touch the test window here.

Before the handover, ask a colleague to review the method the way code is reviewed: any feature that will not exist at prediction time, a split that lets the future in, and the ceiling. These mistakes stay hidden until late unless someone else looks. `doubting-results` lists the checks.

## Stop signs

- A fit before the candidate cards and the comparison rule are written.
- A feature run before the keep rule is written.
- A step started before the owner said go, or, working alone, a stop with no open decision in the log.
- A rule, grid or tie-break changed after its result was seen, with no deviation in the log.
- Validation far above the rule or above what similar products achieve: run `doubting-results` before going further.
- No model beats the trivial baseline: the data holds little signal for this label; go back to `framing-models`.
- The best model beats the simple one by less than the noise between folds.
- A feature in the chosen model that no run shows earning its place.
- A feature dropped because a linear model gained nothing from it, never compared in a model that can combine features.
- A result that cannot be rebuilt from its record.
