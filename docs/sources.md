# Sources

The skills are written from seven sources, each read in full on 2026-10-19.
This file says which sections each skill draws on, where the sources
disagree and how the skills settle it, and what was left out. Rules are cited
as *(Rules of ML #n)*.

| Source | Author | Version read | License |
|---|---|---|---|
| [Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course) | Google for Developers | pages updated 2025-08-25 to 2026-04-09 | CC BY 4.0 |
| [Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml) | Martin Zinkevich | updated 2025-08-25 | CC BY 4.0 |
| [Machine Learning Knowledge Base](https://0trm.dev/mlkb/) (mlkb) | Tomás Ravalli, from Ng's *Machine Learning in Production*, Géron, Zinkevich and Eugene Yan | October 2026 | the author's notes |
| [Machine Learning Systems Design](https://huyenchip.com/machine-learning-systems-design/toc.html) | Chip Huyen | 2019 | © Chip Huyen; linked, not copied |
| [Introduction to Machine Learning Interviews Book](https://huyenchip.com/ml-interviews-book/) | Chip Huyen | 2021 | © Chip Huyen; linked, not copied |
| [MLFlow Crash Course: MLOps in Python](https://www.youtube.com/watch?v=4FgAKzM_uYM) | NeuralNine | 2026-05-25, 42 min | YouTube |
| [MLflow-crash-course](https://github.com/Morikashi/MLflow-crash-course) | Morikashi | last commit 2025-06-01, written for MLflow 2.x | Apache 2.0 |

The MLflow material is checked against the [MLflow 3 documentation](https://mlflow.org/docs/latest/).
The skills name no tool: MLflow is the worked example, not the method.

## By skill

### routing-requests

- Rules of ML #1 to #3: a rule ships before a model, and a model replaces a rule once the rule turns complex. #12 and #13: the objective is simple, observable and attributable, with a policy layer on top. #25: a model is judged by what the prediction is used for. #38 and #39: launch decisions are proxies for long-term goals, and a refused launch revises the objective.
- mlkb [2.1 Scoping](https://0trm.dev/mlkb/design/scoping.html): the business problem before the AI problem, feasibility from human-level performance or predictive features, value through the bridge from the ML metric to the business metric, and timeboxes per phase.
- Huyen, systems design, [project setup](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#project-setup-zlkQIG9): goals, how users meet the prediction, performance constraints, and whether a false positive or a false negative costs more.
- Interviews book [1.1.3.1 Production cycle](https://huyenchip.com/ml-interviews-book/contents/1.1.3.1-production-cycle.html): every step loops back, and a failure after launch can send the work back to the metric. [7.1](https://huyenchip.com/ml-interviews-book/contents/7.1-basics.html) Q15: good on test, poor in production, worked as hypotheses before remedies.
- Crash Course [AutoML: benefits and limitations](https://developers.google.com/machine-learning/crash-course/automl/benefits-limitations): a tool that cannot build even a mediocre model is a sign the data holds little signal.

### building-training-data

- mlkb [2.2 Data](https://0trm.dev/mlkb/design/data.html): consistent labels, human-level performance as agreement between labelers, the four dimensions of data quality, provenance and lineage. [3.2.4](https://0trm.dev/mlkb/development/validation-and-tuning.html): the split follows the data's time order.
- Rules of ML #6: copied pipelines drop data. #11: feature owners. #17: observed features before learned ones. #29 to #32: log serving features, importance-weight samples, beware joined tables that change, share code between training and serving. #33: test on the days after training. #34 to #36: held-out traffic for filters, the skew ranking creates, positional features.
- Crash Course: [numerical data](https://developers.google.com/machine-learning/crash-course/numerical-data), [categorical data](https://developers.google.com/machine-learning/crash-course/categorical-data), and [datasets, generalization and overfitting](https://developers.google.com/machine-learning/crash-course/overfitting) (labels, imbalanced datasets, dividing datasets, transforming data). Production: [when to transform data](https://developers.google.com/machine-learning/crash-course/production-ml-systems/transforming-data) and [monitoring pipelines](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring) (label leakage, training-serving skew). Fairness: [types of bias](https://developers.google.com/machine-learning/crash-course/fairness/types-of-bias) and [identifying bias](https://developers.google.com/machine-learning/crash-course/fairness/identifying-bias).
- Interviews book [7.2 Sampling and creating training data](https://huyenchip.com/ml-interviews-book/contents/7.2-sampling-and-creating-training-data.html): which rows to label, the audit sample for labels, selection bias, leakage, duplicates, missing values, imbalance.
- Huyen, systems design, [data pipeline](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#data-pipeline-698WI4R): availability, annotation, storage, privacy, biases.

### training-models

- mlkb [3.1 Modeling overview](https://0trm.dev/mlkb/development/modeling-overview.html), [3.2 Validation and tuning](https://0trm.dev/mlkb/development/validation-and-tuning.html), [3.3 Model baseline](https://0trm.dev/mlkb/development/model-baseline.html), [3.6 Skewed datasets](https://0trm.dev/mlkb/development/skewed-datasets.html).
- Rules of ML #4: a simple first model and the infrastructure right. #14: an interpretable, calibrated model first. #16: plan to launch and iterate. #18 to #22: features. #40: simple ensembles.
- Crash Course [classification](https://developers.google.com/machine-learning/crash-course/classification) (thresholds, accuracy, precision and recall, ROC and AUC, prediction bias), [linear regression](https://developers.google.com/machine-learning/crash-course/linear-regression) (loss, hyperparameters), [logistic regression](https://developers.google.com/machine-learning/crash-course/logistic-regression), and overfitting ([model complexity](https://developers.google.com/machine-learning/crash-course/overfitting/model-complexity), [regularization](https://developers.google.com/machine-learning/crash-course/overfitting/regularization), [loss curves](https://developers.google.com/machine-learning/crash-course/overfitting/interpreting-loss-curves)).
- Huyen, systems design, [modeling](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#modeling-o97BIGR): the simplest model that does the job, the random, human and heuristic baselines, debugging (start simple, overfit a single batch, set a seed), tuning.
- Interviews book [7.3 Objective functions, metrics and evaluation](https://huyenchip.com/ml-interviews-book/contents/7.3-objective-functions,-metrics,-and-evaluation.html), [8.1 Classical machine learning](https://huyenchip.com/ml-interviews-book/contents/8.1.1-overview:-basic-algorithm.html), [8.3 Training neural networks](https://huyenchip.com/ml-interviews-book/contents/8.3-training-neural-networks.html).
- MLflow video, 33:20 and 37:17: a search kept as one parent run with a child per trial, and the curves per epoch that show overfitting.

### analyzing-errors

- mlkb [3.4 Error analysis](https://0trm.dev/mlkb/development/error-analysis.html), [3.5 Prioritizing improvements](https://0trm.dev/mlkb/development/prioritizing-improvements.html), [3.7 Performance auditing](https://0trm.dev/mlkb/development/performance-auditing.html), [3.8 Data-centric development](https://0trm.dev/mlkb/development/data-centric-development.html).
- Rules of ML #23 to #28: you are not a typical end user, the delta between models, utilitarian performance, errors turned into features, undesirable behavior quantified, short-term behavior that differs from long-term. #41 to #43: what to do on a plateau.
- Crash Course fairness: [evaluating for bias](https://developers.google.com/machine-learning/crash-course/fairness/evaluating-for-bias), [demographic parity](https://developers.google.com/machine-learning/crash-course/fairness/demographic-parity), [equality of opportunity](https://developers.google.com/machine-learning/crash-course/fairness/equality-of-opportunity), [counterfactual fairness](https://developers.google.com/machine-learning/crash-course/fairness/counterfactual-fairness), [mitigating bias](https://developers.google.com/machine-learning/crash-course/fairness/mitigating-bias). Production: data slices in [monitoring pipelines](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring).
- Interviews book [1.1.1](https://huyenchip.com/ml-interviews-book/contents/1.1.1-working-in-research-vs.-workingin-production.html): requirements beyond accuracy (latency, interpretability, fairness, adaptability). [5.2.1.2](https://huyenchip.com/ml-interviews-book/contents/5.2.1.2-questions.html) Q23: small slices swing by chance.

### launching-models

- mlkb [4.1 Key challenges](https://0trm.dev/mlkb/deployment/key-challenges.html) (real-time or batch, cloud or edge, latency, throughput, logging), [4.2 Architecture](https://0trm.dev/mlkb/deployment/architecture.html), [4.3 Deployment patterns](https://0trm.dev/mlkb/deployment/deployment-patterns.html) (shadow, canary, blue-green, degrees of automation, launch decisions), [4.4 Reproducibility and CI/CD](https://0trm.dev/mlkb/deployment/reproducibility-cicd.html) (pre-export checks, the model build pipeline).
- Rules of ML #5: test the infrastructure apart from the model. #9: detect problems before exporting. #24 and #39.
- Crash Course production: [static vs dynamic training](https://developers.google.com/machine-learning/crash-course/production-ml-systems/static-vs-dynamic-training), [static vs dynamic inference](https://developers.google.com/machine-learning/crash-course/production-ml-systems/static-vs-dynamic-inference), [deployment testing](https://developers.google.com/machine-learning/crash-course/production-ml-systems/deployment-testing).
- Huyen, systems design, [serving](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#serving-091rIYw) (confidence, a human for low-confidence cases, device or server, interpretability, misuse) and [case studies](https://huyenchip.com/machine-learning-systems-design/case-studies.html) (Booking.com: model performance is not business performance; test impact with randomized trials).
- Interviews book 7.1 Q14: deploying large models. [8.3](https://huyenchip.com/ml-interviews-book/contents/8.3-training-neural-networks.html) Q28 to Q30: pruning, training data recoverable from checkpoints, distillation.
- MLflow-crash-course [notebook 3](https://github.com/Morikashi/MLflow-crash-course/blob/main/Notebook_3_Model_Registry_and_Production_Deployment.ipynb): an alias as the switch serving reads, a signature as the input contract.

### monitoring-models

- mlkb 4.1 (concept drift and data drift), [4.5 Monitoring](https://0trm.dev/mlkb/deployment/monitoring.html) (software and statistical metrics, thresholds, pipeline monitoring, rate of change, how often to retrain, training-serving skew).
- Rules of ML #8: freshness requirements. #10: failures that raise no error. #37: skew measured in three parts.
- Crash Course production: [monitoring pipelines](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring) (schema, slices, real-world metrics, model age, system health, quality on unlabeled data) and [questions to ask](https://developers.google.com/machine-learning/crash-course/production-ml-systems/questions) (features worth their upkeep, upstream reliability, feedback loops).
- Interviews book 7.1 Q13 and Q15: why performance degrades in production. 7.2 Q8: comparing training and live distributions. [5.2.2](https://huyenchip.com/ml-interviews-book/contents/5.2.2-stats.html) Q17: many comparisons raise alarms by chance.

### tracking-models

- mlkb [3.9 Experiment tracking](https://0trm.dev/mlkb/development/experiment-tracking.html), 4.4 (each model's record, data profiles, versioning, the model package), [Templates](https://0trm.dev/mlkb/templates.html) (one-pager, design doc, after-action review), [1.4 MLOps](https://0trm.dev/mlkb/overview/mlops.html) (maturity levels).
- MLflow video, 1:07 to 41:20 on classic ML, and MLflow-crash-course notebooks [1](https://github.com/Morikashi/MLflow-crash-course/blob/main/Notebook_1_Getting_Started_with_MLFlow.ipynb) to 3: runs, parameters, metrics, artifacts, nested runs, signatures, the registry and its aliases.
- MLflow docs: [datasets](https://mlflow.org/docs/latest/ml/dataset/) named by content digest, [the model registry](https://mlflow.org/docs/latest/ml/model-registry/) (versions linked to runs, aliases as pointers), [evaluation](https://mlflow.org/docs/latest/ml/evaluation/) (results tied to a version, thresholds against a baseline).
- Crash Course [deployment testing](https://developers.google.com/machine-learning/crash-course/production-ml-systems/deployment-testing): reproducible training (seeds, version control from the first iteration). Monitoring pipelines: hash on keys that do not change.

## Where the sources disagree

1. **The split.** The Crash Course shuffles, then partitions. Rules of ML #33, mlkb 3.2.4 and the interviews book (7.2 Q15 and Q18) split by time. The skills split by time whenever rows are time-ordered; shuffling is safe only under the Crash Course's own conditions for generalizing, stationary data with independent rows.
2. **AUC.** The Crash Course compares models by AUC on roughly balanced data, and Rules of ML #9 gates export on it. gallop's `building-models` says AUC on its own validates nothing. The skills use AUC to compare two models and judge a ship decision at the threshold the product uses.
3. **Overlap between training and test.** The Crash Course calls test sets with no overlap in their keys artificially hard. A split by time keeps entities on both sides of the cutoff, unless the product mostly scores entities it has never seen.
4. **Baseline.** The Crash Course's baseline is a first model on one or two features, a check that the pipeline works. Huyen's random, human and heuristic baselines, mlkb's human-level performance and gallop's base rate are the bar to beat. `training-models` keeps both and names which one a number is compared against.
5. **MLflow versions.** The notebooks use registry stages and `mlflow.evaluate`; the MLflow docs mark stages deprecated since 2.9 and `mlflow.evaluate` since 3.0. The video reads autolog metrics, which are computed on the training data. The skills stay tool-neutral, and a number computed on training data is never evidence.
6. **Ownership.** The interviews book's production cycle puts deployment and monitoring under MLOps, not ML engineering. The skills make the decisions; who runs the infrastructure is the team's call.

## Left out

- **GenAI:** the Crash Course LLM module, the video from 6:11 to 29:30 (tracing, GenAI evaluation, prompt templates, gateways, agent servers) and notebooks 4 to 8. What carries over: a fallback when a model or provider fails, versions that never change once recorded, and a production server in place of a development one.
- **Interviews and careers:** most of the interviews book's Part I (hiring, compensation, interview formats) and the booklet's 27 practice exercises.
- **Math and computer science refreshers:** chapters 5 and 6 of the interviews book, except the base-rate and small-numbers questions, and the derivations in the Crash Course.
- **ML platform work:** distributed training and scaling, feature stores built for other teams, serving infrastructure.
- **Unsupervised models:** clustering and anomaly detection, where the label and split logic does not hold.
- **Not available:** the answers to the Crash Course badge quizzes and to the interviews book's questions are not published, and the Crash Course generalization video has no transcript.
