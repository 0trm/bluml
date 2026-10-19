<p align="center">
  <img src="assets/safflowers.jpg" width="235" alt="Safflowers by Ono Chikkyō: three stems on a blue ground, two in orange bloom and one in bud">
</p>

<h1 align="center">saffML</h1>

<p align="center">
  <strong>Skills that make your coding agent think like a product ML engineer.</strong><br>
  From the decision a model serves to the day it needs replacing.
</p>

<p align="center">
  <a href="#how-it-works">how it works</a> &middot; <a href="#skills">skills</a> &middot; <a href="#does-it-help">evals</a> &middot; <a href="#install">install</a>
</p>

## Why

Ask a coding agent for a model and it will train one. The code runs, a metric prints, and nothing in the output says that the split shuffled time, that a column was backfilled from the future, that the threshold was left at 0.5, or that the service sends prices in cents. In product ML these are the failures that decide whether a feature works, and none of them raises an error.

saffml gives the agent the habits of an engineer who has shipped models into products: ask what the prediction will decide before training anything, beat the rule before beating a model, distrust a good number until the split and the features are checked, launch in steps that can be taken back, and find the cause before retraining.

## Five laws

1. **Ship a rule first.** It is the baseline to beat and the pipeline that collects the labels.
2. **Write the metric ladder down before training anything.** The number the model moves has to move the number the business cares about.
3. **Better data beats a cleverer model,** and a leak makes any model look better than it is.
4. **A threshold is a product decision.** Set it with the people who pay for each kind of error.
5. **Assume the live model is getting worse right now,** and keep the instruments that would show it.

## How it works

Every model gets one file, `MODEL.md`, next to its code. Each skill reads it first and writes its section last: the decision and what each error costs, the design review, the data, the runs, the verdict, the launch, the incidents. Each section ends at a gate, a short checklist that needs evidence, and a stage starts only when the gate before it is ticked. The file is how a model's reasoning survives between sessions, between people and between versions. A filled example follows a delivery-time model from framing to its first incident: its [MODEL.md](examples/delivery-eta/MODEL.md) and its [design doc](examples/delivery-eta/DESIGN.md).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/map-dark.svg">
    <img src="docs/map-light.svg" width="600" alt="The saffml map, a flowchart. It starts at a request for a model, which is framed, then a decision: is a model worth it? If not, the rule ships. If so, the work goes through design, data, train, evaluate, launch and monitor, then a decision: is the model still paying? If not, it is retired to the rule; if so, monitoring continues. Dashed arrows loop back: a rejected design and a lost online test return to framing, a model that loses to the rule returns to data, and a live model returns to training when the world moves and to data when an input breaks.">
  </picture>
</p>

Solid arrows are the main path, and each step on it ends at a gate; dashed arrows are the ways work loops back. Before anything is built, a design doc goes through a rough pre-review and then a formal review, where design flaws are cheapest to fix. Work loops back: a rejected design returns to framing, errors point at the data, a live model goes back to training when the world moves and to the pipeline when an input breaks; a launch that loses its online test sends the objective back to framing, and a live model that stops paying for itself is retired to the rule. `doubting-results` runs across all of it, wherever a number is about to be reported.

## Skills

| Skill | What it decides | Reach for it when |
|---|---|---|
| [`framing-models`](skills/framing-models/SKILL.md) | What the product does with each prediction, what each error costs and who owns the threshold, the rule to beat and its number, and the business case: whether the gain pays for the model's build, upkeep, compute and latency, with its break-even gain and payback | someone asks for a model, a request names a model before the decision it serves, or someone asks whether a model is worth it |
| [`writing-design-docs`](skills/writing-design-docs/SKILL.md) | Why now and how success is measured, quantified requirements, the methodology and the implementation, the risks, the alternatives rejected, and what the reviewers must decide | a framed model is ambiguous, high impact or more than a few days of work, or someone asks for a design doc, spec or proposal |
| [`building-datasets`](skills/building-datasets/SKILL.md) | The prediction time, the label and when it is known, features as they stood then, a split that mirrors serving, and the bias the product put in its own labels | assembling training data, choosing a label or a split, or when one column predicts suspiciously well |
| [`training-models`](skills/training-models/SKILL.md) | The baselines, the simplest model that beats them, how it is debugged and tuned without the test set, and the record that rebuilds it | fitting, comparing or tuning models, or when a model will not beat a simple baseline |
| [`evaluating-models`](skills/evaluating-models/SKILL.md) | The operating point from costs or capacity, the gain over the rule in the product's unit with its interval, whether that gain clears break-even, the slices where it loses, and the next fix | choosing a threshold, comparing with the rule, or deciding whether a model is ready |
| [`launching-models`](skills/launching-models/SKILL.md) | Batch or online, the input contract, proof that serving computes what training did, the rollout ladder, the online test's decision rule, and the rollback | a model is about to replace a rule or an older model, or an offline gain is offered as the reason to ship |
| [`monitoring-models`](skills/monitoring-models/SKILL.md) | What to watch on inputs, outputs and outcomes, how fresh the model must stay, the cause of a change named before the fix, and whether the model still pays for itself | a live number moves, someone asks to retrain, a model has no alerts, or its costs change |
| [`doubting-results`](skills/doubting-results/SKILL.md) | Whether a number can be trusted: leaks, splits, reused test sets, training-data metrics, the wrong comparison, missing intervals | before any model number is reported, and whenever a result beats expectations |

Four skills carry tested Python checks, run by the agent rather than rewritten each time: a [leak screen](skills/building-datasets/scripts/leakage_screen.py), a [cost and capacity threshold](skills/evaluating-models/scripts/threshold.py), a [slice comparison with paired intervals](skills/evaluating-models/scripts/slices.py) and a [drift report](skills/monitoring-models/scripts/drift.py).

## Does it help?

Seven requests with traps planted in synthetic data, each run three times with saffml and three times without, and scored by an LLM judge against five or six criteria. A score is the weighted share of criteria met. Method, criteria and caveats: [evals/](evals/README.md).

| Case | Sonnet with | without | Opus with | without |
|---|---|---|---|---|
| `design-doc` | 0.93 | 0.63 | 1.00 | 0.89 |
| `rule-first` | 0.58 | 0.42 | 0.96 | 0.33 |
| `churn-leak` | 1.00 | 1.00 | 1.00 | 1.00 |
| `fraud-threshold` | 0.89 | 0.56 | 1.00 | 0.63 |
| `ranker-clicks` | 0.96 | 0.96 | 0.96 | 1.00 |
| `ship-it` | 1.00 | 0.96 | 1.00 | 1.00 |
| `ctr-drop` | 0.96 | 0.88 | 1.00 | 0.88 |
| **Mean** | **0.90** | **0.77** | **0.99** | **0.82** |

Without saffml, both models already catch the textbook traps: a backfilled column, position bias in clicks, prices sent in cents. What they skip is the product reasoning around the model. Neither compared the fraud model with the rule slice by slice, and neither noticed that it ranks new customers far worse (0 of 6 runs; 5 of 6 with saffml). Opus never weighed a ticket-routing model against the keyword rule that nearly matches it (0 of 3; 3 of 3), and none of Sonnet's design docs both put numbers on the requirements and questioned the brief's "updated live" (0 of 3; 3 of 3). One gap remains: Sonnet with saffml still skips the rule-against-model weighing in every run.

## Install

As a Claude Code plugin:

```text
/plugin install saffml --marketplace 0trm/saffml
```

Or copy the skills into a project:

```bash
git clone https://github.com/0trm/saffml
mkdir -p .claude/skills
cp -r saffml/skills/* .claude/skills/
```

The scripts need Python 3.10 or later with numpy and pandas; `uv run <script>` installs them. Run their tests with `uv run --with numpy,pandas,pytest pytest tests`.

## Scope

saffml covers supervised models that run inside a product: a classifier, a ranker or a forecast whose output the product acts on. LLM applications, research, ML platform work and unsupervised models are out of scope. What each skill is written from, and where its sources disagree: [docs/sources.md](docs/sources.md).

## License

[MIT](LICENSE) for the text and code. The painting in `assets/` is not covered by it: it is Ono Chikkyō (小野竹喬, 1889–1979), *For Haiku Poems in Bashō's Narrow Road to a Far Province: "A lady's eyebrow brush / came to mind when I saw / safflowers in bloom"* (奥の細道句抄絵 まゆはきを俤にして紅粉の花), 1976, color on paper, The National Museum of Modern Art, Kyoto ([collection record](https://artplatform.go.jp/collections/W316214)).
