# Run records

Every number in `MODEL.md` points to a run that can be rebuilt. The tool matters less than the record.

## Contents

- What a run records
- A minimal record without a tracker
- The same record in MLflow
- Promotion and rollback

## What a run records

| Field | Why |
|---|---|
| Run id | The handle `MODEL.md` cites |
| Code version | The commit that produced the model |
| Data version | A content hash or snapshot id of the training table, plus the split boundaries |
| Parameters and seed | So the run can be repeated |
| Operating point | The threshold or k that turns scores into decisions, so a release can be traced to the decisions it made |
| Validation result at the operating point, with the baseline's on the same rows | The comparison that matters |
| Model file and its input signature | What serving loads, and the inputs it expects (names, types, units) |
| Notes | What was tried and why it was kept or dropped |

## A minimal record without a tracker

Append one line per run to `runs.csv` beside the code:

```text
run_id,commit,data_hash,params,seed,operating_point,metric,value,baseline_value,model_path,note
2026-10-19-a,3f2c1e9,sha256:9a1c...,depth=6;lr=0.05;trees=400,7,top40/week,won_deals_top40,11.2,9.8,models/a.joblib,"beats the stage rule"
```

Hash the training table with `sha256sum train.parquet` or `hashlib.sha256(path.read_bytes())`.

## The same record in MLflow

MLflow 3 calls these runs, datasets and logged models. A run with its dataset, parameters, metrics and model:

```python
import mlflow

mlflow.set_experiment("lead-scoring")
with mlflow.start_run(run_name="gbm-depth6") as run:
    mlflow.log_input(mlflow.data.from_pandas(train_df, name="train", targets="won"), context="training")
    mlflow.log_params({"max_depth": 6, "learning_rate": 0.05, "n_estimators": 400, "seed": 7, "operating_point": "top40/week"})
    mlflow.log_metric("val_won_deals_top40", 11.2)
    mlflow.log_metric("val_rule_won_deals_top40", 9.8)
    mlflow.sklearn.log_model(model, name="model", input_example=X_val.head(5))
```

Notes for MLflow users:

- `mlflow.data.from_pandas` records a digest of the table's content, so two runs on different data are told apart.
- An input example lets MLflow infer the model's signature: the input contract serving will check.
- Autologged training metrics are computed on training data. Log validation metrics yourself.
- Registry stages are deprecated since MLflow 2.9; use aliases such as `@champion` and `@challenger`, which serving reads to choose a version.
- For a search, log one parent run with a child run per trial (`mlflow.start_run(nested=True)`).

## Promotion and rollback

A model version is promoted by moving an alias (or a config value) that serving reads, never by editing code. The previous version keeps its own alias so a rollback is the same one-line move. Record each move, with the evidence for it, in the `MODEL.md` log.
