# Debugging a model

Symptoms, their usual causes, and the check that tells them apart. Start with the cheapest check.

| Symptom | Usual causes | Check |
|---|---|---|
| Cannot overfit 100 rows | Labels misaligned with features after a join or a sort; a bug in the loss; features all missing or constant | Print ten rows with their labels and read them; check the join keys; train on a single feature that should work |
| Loss does not fall | Learning rate too high or too low; unscaled inputs for a linear or neural model; a label column of the wrong type | Try learning rates a factor of 10 apart; scale inputs; check the label's values |
| Training loss falls, validation rises | Overfitting: too many trees, too deep, too many features for the rows (Rules of ML #21) | Stop earlier; regularize; fewer or coarser features |
| Validation better than training | Regularization active only in training (dropout); validation easier than training (a different period); leakage into validation | Compare training and validation distributions; rerun the leak screen on the validation rows |
| Score far better than expected | A leak | Run the leak screen; retrain without the top feature; split by time |
| Every row gets nearly the same score | A feature pipeline that returns constants at scoring time; extreme class imbalance with no signal | Plot the score distribution; check features at scoring time |
| Mean prediction differs from the actual rate | Resampled training data; label distribution shift between training and validation; a bug in a feature | Compare the mean score with the base rate in each split; recalibrate |
| Good on validation, poor on the next period | Features that drift; a validation window too similar to training; seasonality | Rolling backtest; compare strength by period |
| Results change between runs | Unfixed seeds; nondeterministic parallel training; data order | Fix every seed; run three times and report the spread |

## Reading feature importance

Importance tells you what the model relies on, not what causes the outcome. Use it to find leaks (one feature dominating) and broken features (an important feature that is constant at serving time). For a model people must explain, prefer a model that is readable by construction over explaining a black box after the fact.

## The plateau

When the model stops improving, the next gain usually comes from new information rather than tuning (Rules of ML #41): a new source of signal, cleaner labels, or more data on the slice where errors cluster. `evaluating-models` finds which, through error analysis.
