<p align="center">
  <img src="assets/safflowers.jpg" width="640" alt="A painting of three safflowers on a blue ground: two stems in orange bloom and one in bud">
</p>

<h1 align="center">saffml</h1>

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

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/map-dark.svg">
  <img src="docs/map-light.svg" width="100%" alt="The saffml map: a request goes to frame, which either ships the rule or passes a gate to design, where a design doc is reviewed, then data, train, evaluate, launch and live, each step behind a gate. A rejected design goes back to framing; errors loop from evaluate back to data; a live model loops back to training when the world moves and to data when an input breaks. doubting-results sits above the whole path and MODEL.md below it.">
</picture>

Before anything is built, a design doc goes through a rough pre-review and then a formal review, where design flaws are cheapest to fix. Work loops back: a rejected design returns to framing, errors point at the data, a live model goes back to training when the world moves and to the pipeline when an input breaks; a launch that loses its online test sends the objective back to framing. `doubting-results` runs across all of it, wherever a number is about to be reported.

## Skills

| Skill | What it decides | Reach for it when |
|---|---|---|
| [`framing-models`](skills/framing-models/SKILL.md) | What the product does with each prediction, what each error costs and who owns the threshold, the rule to beat and its number, and whether a model is worth building | someone asks for a model, or a request names a model before the decision it serves |
| [`writing-design-docs`](skills/writing-design-docs/SKILL.md) | Why now and how success is measured, quantified requirements, the methodology and the implementation, the risks, the alternatives rejected, and what the reviewers must decide | a framed model is ambiguous, high impact or more than a few days of work, or someone asks for a design doc, spec or proposal |
| [`building-datasets`](skills/building-datasets/SKILL.md) | The prediction time, the label and when it is known, features as they stood then, a split that mirrors serving, and the bias the product put in its own labels | assembling training data, choosing a label or a split, or when one column predicts suspiciously well |
| [`training-models`](skills/training-models/SKILL.md) | The baselines, the simplest model that beats them, how it is debugged and tuned without the test set, and the record that rebuilds it | fitting, comparing or tuning models, or when a model will not beat a simple baseline |
| [`evaluating-models`](skills/evaluating-models/SKILL.md) | The operating point from costs or capacity, the gain over the rule in the product's unit with its interval, the slices where it loses, and the next fix | choosing a threshold, comparing with the rule, or deciding whether a model is ready |
| [`launching-models`](skills/launching-models/SKILL.md) | Batch or online, the input contract, proof that serving computes what training did, the rollout ladder, the online test's decision rule, and the rollback | a model is about to replace a rule or an older model, or an offline gain is offered as the reason to ship |
| [`monitoring-models`](skills/monitoring-models/SKILL.md) | What to watch on inputs, outputs and outcomes, how fresh the model must stay, and the cause of a change named before the fix | a live number moves, someone asks to retrain, or a model has no alerts |
| [`doubting-results`](skills/doubting-results/SKILL.md) | Whether a number can be trusted: leaks, splits, reused test sets, training-data metrics, the wrong comparison, missing intervals | before any model number is reported, and whenever a result beats expectations |

Four skills carry tested Python checks, run by the agent rather than rewritten each time: a [leak screen](skills/building-datasets/scripts/leakage_screen.py), a [cost and capacity threshold](skills/evaluating-models/scripts/threshold.py), a [slice comparison with paired intervals](skills/evaluating-models/scripts/slices.py) and a [drift report](skills/monitoring-models/scripts/drift.py).

## Does it help?

<!-- eval-results -->

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

[MIT](LICENSE) for the text and code. The painting in `assets/` is not covered by it.
