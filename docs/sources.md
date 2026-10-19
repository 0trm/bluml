# Sources

The skills are written from nine sources, read in full in October 2026, and tested against the scenarios in [`evals/`](../evals). This page says which sections each skill draws on, where the sources disagree and how the skills settle it, and what was left out. Rules are cited as *Rules of ML #n*.

| Source | Author | Version read | License |
|---|---|---|---|
| [Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course) | Google for Developers | pages updated 2025-08-25 to 2026-04-09 | CC BY 4.0 |
| [Rules of Machine Learning](https://developers.google.com/machine-learning/guides/rules-of-ml) | Martin Zinkevich | updated 2025-08-25 | CC BY 4.0 |
| [Machine Learning Knowledge Base](https://0trm.dev/mlkb/) (mlkb) | Tomás Ravalli, from Ng's *Machine Learning in Production*, Géron, Zinkevich and Eugene Yan | October 2026 | the author's notes |
| *ML Engineering 101: Building ML into Products* | Tomás Ravalli | lecture notes, 2026-10-08 | the author's notes |
| [Machine Learning Systems Design](https://huyenchip.com/machine-learning-systems-design/toc.html) | Chip Huyen | 2019 | © Chip Huyen; linked, not copied |
| [Introduction to Machine Learning Interviews Book](https://huyenchip.com/ml-interviews-book/) | Chip Huyen | 2021 | © Chip Huyen; linked, not copied |
| [How to Write Design Docs for Machine Learning Systems](https://eugeneyan.com/writing/ml-design-docs/), with its [template](https://github.com/eugeneyan/ml-design-docs) | Eugene Yan | March 2021; template updated 2023-03-16 | © Eugene Yan; the template repo has no license, so it is linked, not copied |
| [MLFlow Crash Course: MLOps in Python](https://www.youtube.com/watch?v=4FgAKzM_uYM) | NeuralNine | 2026-05-25, 42 min | YouTube |
| [MLflow-crash-course](https://github.com/Morikashi/MLflow-crash-course) | Morikashi | last commit 2025-06-01, written for MLflow 2.x | Apache 2.0 |

The MLflow material is checked against the [MLflow 3 documentation](https://mlflow.org/docs/latest/). The skills name MLflow only as a worked example. The skill format follows Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), and the evals run on [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals).

## By skill

### framing-models

- *ML Engineering 101*, parts 2 and 3: ship a heuristic first; the four conditions under which ML earns its place; the metric ladder; thresholds as product decisions; the delivery-estimate case study.
- Rules of ML #1 to #3: launch without ML; metrics first; ML over a complex heuristic. #12 and #13: a simple, observable, attributable objective. #25: utilitarian performance over predictive power.
- mlkb [2.1 Scoping](https://0trm.dev/mlkb/design/scoping.html): the business problem before the AI problem; feasibility; the bridge from the ML metric to the business metric.
- Huyen, systems design, [project setup](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#project-setup-zlkQIG9): goals, how users meet the prediction, which error costs more.
- Crash Course [AutoML: benefits and limitations](https://developers.google.com/machine-learning/crash-course/automl/benefits-limitations): a tool that cannot build even a mediocre model signals little predictive signal.

### writing-design-docs

- Eugene Yan, [How to Write Design Docs for Machine Learning Systems](https://eugeneyan.com/writing/ml-design-docs/): why and when to write one (ambiguous, high impact or high effort); the why and what (motivation, success criteria, functional and non-functional requirements, scope, assumptions); the methodology (problem statement, data, techniques, validation and experimentation, humans in the loop); the implementation (high-level design, infra and scale, performance, security, privacy, monitoring, cost, integration, risks); alternatives; a rough pre-review before the formal review. saffml's template and reviewer checklist follow this structure in its own words.
- mlkb [Templates](https://0trm.dev/mlkb/templates.html): one-pager, design doc and after-action review, and where each falls in the lifecycle: the design doc before building, while changes are cheap.
- Rules of ML #39: launch decisions are a proxy for long-term goals, so the doc names the product metric the online test decides on.

### building-datasets

- mlkb [2.2 Data](https://0trm.dev/mlkb/design/data.html): consistent labels, provenance and lineage; [3.2.4](https://0trm.dev/mlkb/development/validation-and-tuning.html): splits that follow time.
- Rules of ML #6: dropped data in copied pipelines. #29 to #32: log serving features, importance-weight samples, joined tables that change, shared code. #33: test on the days after training. #34 to #36: held-out traffic for filters, the skew ranking creates, positional features.
- Crash Course: [datasets, generalization and overfitting](https://developers.google.com/machine-learning/crash-course/overfitting) (labels, imbalance, dividing data); production [monitoring pipelines](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring) (label leakage, training-serving skew); fairness [types of bias](https://developers.google.com/machine-learning/crash-course/fairness/types-of-bias).
- Interviews book [7.2 Sampling and creating training data](https://huyenchip.com/ml-interviews-book/contents/7.2-sampling-and-creating-training-data.html): selection bias, leakage, duplicates, imbalance.
- *ML Engineering 101*, part 3: leakage, splits, training-serving skew, the data flywheel; part 5: feedback loops and exploration traffic.

### training-models

- mlkb [3.1 Modeling overview](https://0trm.dev/mlkb/development/modeling-overview.html), [3.2 Validation and tuning](https://0trm.dev/mlkb/development/validation-and-tuning.html), [3.3 Model baseline](https://0trm.dev/mlkb/development/model-baseline.html), [3.6 Skewed datasets](https://0trm.dev/mlkb/development/skewed-datasets.html), [3.9 Experiment tracking](https://0trm.dev/mlkb/development/experiment-tracking.html).
- Rules of ML #4: a simple first model and the infrastructure right. #14: interpretable models first. #16 to #22: features. #40: simple ensembles. #41: new information on a plateau.
- Crash Course [classification](https://developers.google.com/machine-learning/crash-course/classification) (prediction bias), [logistic regression](https://developers.google.com/machine-learning/crash-course/logistic-regression), [loss curves](https://developers.google.com/machine-learning/crash-course/overfitting/interpreting-loss-curves) and [regularization](https://developers.google.com/machine-learning/crash-course/overfitting/regularization).
- Huyen, systems design, [modeling](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#modeling-o97BIGR): random, human and heuristic baselines; overfit a single batch; set a seed.
- MLflow video (33:20, 37:17) and the MLflow-crash-course [notebooks](https://github.com/Morikashi/MLflow-crash-course): runs, nested runs for searches, signatures. MLflow 3 docs: [datasets](https://mlflow.org/docs/latest/ml/dataset/) named by content digest, [model registry](https://mlflow.org/docs/latest/ml/model-registry/) aliases.

### evaluating-models

- mlkb [3.4 Error analysis](https://0trm.dev/mlkb/development/error-analysis.html), [3.5 Prioritizing improvements](https://0trm.dev/mlkb/development/prioritizing-improvements.html), [3.7 Performance auditing](https://0trm.dev/mlkb/development/performance-auditing.html), [3.8 Data-centric development](https://0trm.dev/mlkb/development/data-centric-development.html).
- Rules of ML #23 to #28: you are not a typical user; the delta between models; patterns in the errors; quantify undesirable behavior.
- Crash Course [classification](https://developers.google.com/machine-learning/crash-course/classification) (thresholds, the confusion matrix, ROC and AUC) and fairness: [evaluating for bias](https://developers.google.com/machine-learning/crash-course/fairness/evaluating-for-bias), [demographic parity](https://developers.google.com/machine-learning/crash-course/fairness/demographic-parity), [equality of opportunity](https://developers.google.com/machine-learning/crash-course/fairness/equality-of-opportunity), [counterfactual fairness](https://developers.google.com/machine-learning/crash-course/fairness/counterfactual-fairness).
- Interviews book [7.3 Objective functions, metrics and evaluation](https://huyenchip.com/ml-interviews-book/contents/7.3-objective-functions,-metrics,-and-evaluation.html); [5.2.1.2](https://huyenchip.com/ml-interviews-book/contents/5.2.1.2-questions.html): small groups swing by chance.
- *ML Engineering 101*, part 3: compare against a dumb baseline; evaluate on slices; the quantile as the product's promise.

### launching-models

- mlkb [4.1 Key challenges](https://0trm.dev/mlkb/deployment/key-challenges.html), [4.2 Architecture](https://0trm.dev/mlkb/deployment/architecture.html), [4.3 Deployment patterns](https://0trm.dev/mlkb/deployment/deployment-patterns.html) (shadow, canary, blue-green, degrees of automation), [4.4 Reproducibility and CI/CD](https://0trm.dev/mlkb/deployment/reproducibility-cicd.html).
- Rules of ML #5: test the infrastructure apart from the model. #9: detect problems before exporting. #39: launch decisions are a proxy for long-term goals.
- Crash Course production: [static vs dynamic training](https://developers.google.com/machine-learning/crash-course/production-ml-systems/static-vs-dynamic-training), [static vs dynamic inference](https://developers.google.com/machine-learning/crash-course/production-ml-systems/static-vs-dynamic-inference), [deployment testing](https://developers.google.com/machine-learning/crash-course/production-ml-systems/deployment-testing).
- Huyen, systems design, [serving](https://huyenchip.com/machine-learning-systems-design/design-a-machine-learning-system.html#serving-091rIYw) and [case studies](https://huyenchip.com/machine-learning-systems-design/case-studies.html): model performance is not business performance; test impact with randomized trials.
- *ML Engineering 101*, part 4: batch before online; the rollout ladder; keep the old model warm; predictions that change the outcome they predict.
- MLflow-crash-course [notebook 3](https://github.com/Morikashi/MLflow-crash-course/blob/main/Notebook_3_Model_Registry_and_Production_Deployment.ipynb): an alias as the switch serving reads; a signature as the input contract.

### monitoring-models

- mlkb [4.5 Monitoring](https://0trm.dev/mlkb/deployment/monitoring.html): software and statistical metrics, thresholds, how often to retrain, training-serving skew.
- Rules of ML #8: freshness requirements. #10: failures that raise no error. #37: skew measured in three parts.
- Crash Course production: [monitoring pipelines](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring) and [questions to ask](https://developers.google.com/machine-learning/crash-course/production-ml-systems/questions).
- Interviews book [7.1](https://huyenchip.com/ml-interviews-book/contents/7.1-basics.html) Q13 and Q15: why performance degrades in production. [5.2.2](https://huyenchip.com/ml-interviews-book/contents/5.2.2-stats.html) Q17: many comparisons raise alarms by chance.
- *ML Engineering 101*, part 5: monitor inputs, outputs and outcomes; feedback loops.

### doubting-results

Gathers the checks above at the moment an agent reports a number: leaks and splits (`building-datasets`), training-data metrics and run records (`training-models`), operating points, baselines and intervals (`evaluating-models`), and skew (`launching-models`).

## Where the sources disagree

1. **The split.** The Crash Course shuffles, then partitions. Rules of ML #33, mlkb 3.2.4 and the interviews book (7.2) split by time. The skills split by time whenever rows are time-ordered; shuffling is acceptable only under the Crash Course's own conditions: independent, identically distributed rows from a stationary distribution.
2. **AUC.** The Crash Course compares models by AUC, and Rules of ML #9 gates export on it. The skills use AUC to compare candidates and as a sanity check, and judge a ship decision at the operating point the product uses.
3. **Overlap between training and test.** The Crash Course calls test sets with no overlapping keys artificially hard. A time split keeps entities on both sides when the product scores known entities again; the skills add an entity holdout when the product mostly scores new ones.
4. **Baseline.** The Crash Course's baseline is a first model that checks the pipeline. Huyen's random, human and heuristic baselines, mlkb's human-level performance and the lecture's rule are the bar to beat. `training-models` records both kinds and names which one a number is compared against.
5. **MLflow versions.** The notebooks use registry stages and `mlflow.evaluate`; the MLflow docs mark stages deprecated since 2.9 and `mlflow.evaluate` since 3.0. The video reads autologged metrics, which are computed on the training data. The skills use aliases, and a number computed on training data is never evidence.
6. **Ownership.** The interviews book places deployment and monitoring with MLOps, not ML engineering. The skills make the decisions; who runs the infrastructure is the team's call.

## Left out

- **LLM applications:** the Crash Course LLM module, the video from 6:11 to 29:30 and notebooks 4 to 8, and the lecture's section on foundation models. What carries over: a fallback when a model or provider fails, versions that never change once recorded, an eval set before the prompt.
- **Interviews and careers:** most of the interviews book's part I and the booklet's practice exercises.
- **Math and computer science refreshers:** chapters 5 and 6 of the interviews book, except the base-rate and small-numbers questions.
- **ML platform work:** distributed training, feature stores built for other teams, serving infrastructure.
- **Unsupervised models:** clustering and anomaly detection, where the label and split logic does not hold.
- **Not available:** the answers to the Crash Course quizzes and to the interviews book's questions are not published.
