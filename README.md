<p align="center">
  <img src="assets/safflowers.jpg" width="222" alt="bluflowers by Ono Chikkyō: three stems on a blue ground, two in orange bloom and one in bud">
</p>

<h1 align="center">bluML</h1>

<p align="center">
  <strong>Skills that make your coding agent think like a product ML engineer.</strong><br>
</p>

<p align="center">
  <a href="#how-it-works">how it works</a> &middot; <a href="#skills">skills</a> &middot; <a href="#does-it-help">evals</a> &middot; <a href="#install">install</a>
</p>

## Why

bluML gives the agent the habits of an engineer who has shipped models into products: ask what the prediction will decide before training anything, beat the rule before beating a model, distrust a good number until the split and the features are checked, launch in steps that can be taken back, and find the cause before retraining.

## Five laws

1. **Ship a rule first.** It is the baseline to beat and the pipeline that collects the labels.
2. **Write the metric ladder down before training anything.** The number the model moves has to move the number the business cares about.
3. **Better data beats a cleverer model,** and a leak makes any model look better than it is.
4. **A threshold is a product decision.** Set it with the people who pay for each kind of error.
5. **Assume the live model is getting worse right now,** and keep the instruments that would show it.

## How it works

<p align="center">
  <img src="docs/map-light.png" width="816" alt="The bluML map, a flowchart in three phases. It starts at a request for a model. Design: the model is framed, then a decision: is a model worth it? If not, the rule ships. If so, design and data follow. Development: train and evaluate. Deployment: launch and monitor, then a decision: is the model still paying? If not, it is retired to the rule; if so, monitoring continues. Dashed arrows loop back: a rejected design and a lost online test return to framing, a model that loses to the rule returns to data, and a live model returns to training when the world moves and to data when an input breaks.">
</p>

Every model gets one file, `MODEL.md`, next to its code. Each skill reads it first and writes its section last: the decision and what each error costs, the design review, the data, the runs, the verdict, the launch, the incidents. Each section ends at a gate, a short checklist that needs evidence, and a stage starts only when the gate before it is ticked. The file is how a model's reasoning survives between sessions, between people and between versions. A filled example follows a delivery-time model from framing to its first incident: its [MODEL.md](examples/delivery-eta/MODEL.md) and its [design doc](examples/delivery-eta/DESIGN.md).

Solid arrows are the main path, and each step on it ends at a gate; dashed arrows are the ways work loops back. The grey bands group the steps into design, development and deployment. Before anything is built, a design doc goes through a rough pre-review and then a formal review, where design flaws are cheapest to fix. Work loops back: a rejected design returns to framing, errors point at the data, a live model goes back to training when the world moves and to the pipeline when an input breaks; a launch that loses its online test sends the objective back to framing, and a live model that stops paying for itself is retired to the rule. `doubting-results` runs across all of it, wherever a number is about to be reported.

## Skills

| Skill | Reach for it when |
|---|---|
| [`framing-models`](skills/framing-models/SKILL.md) | someone asks for a model, a request names a model before the decision it serves, or someone asks whether a model is worth it |
| [`writing-design-docs`](skills/writing-design-docs/SKILL.md) | a framed model is ambiguous, high impact or more than a few days of work, or someone asks for a design doc, spec or proposal |
| [`building-datasets`](skills/building-datasets/SKILL.md) | assembling training data, choosing a label or a split, when labels are scarce or noisy, or when one column predicts suspiciously well |
| [`training-models`](skills/training-models/SKILL.md) | fitting, comparing or tuning models, or when a model will not beat a simple baseline |
| [`evaluating-models`](skills/evaluating-models/SKILL.md) | choosing a threshold, comparing with the rule, or deciding whether a model is ready |
| [`launching-models`](skills/launching-models/SKILL.md) | a model is about to replace a rule or an older model, or an offline gain is offered as the reason to ship |
| [`monitoring-models`](skills/monitoring-models/SKILL.md) | a live number moves, someone asks to retrain, a model has no alerts, or its costs change |
| [`doubting-results`](skills/doubting-results/SKILL.md) | before any model number is reported, and whenever a result beats expectations |

Four skills carry tested Python checks, run by the agent rather than rewritten each time: a [leak screen](skills/building-datasets/scripts/leakage_screen.py), a [cost and capacity threshold](skills/evaluating-models/scripts/threshold.py), a [slice comparison with paired intervals](skills/evaluating-models/scripts/slices.py) and a [drift report](skills/monitoring-models/scripts/drift.py).

## Does it help?

| | without | with bluML |
|---|--:|--:|
| Sonnet | 0.67 | **0.92** |
| Opus | 0.84 | **0.96** |

<details>
<summary>Per case, and what changed</summary>

Seven requests with traps planted in synthetic data, each run three times with bluML and three times without, and scored by an LLM judge against five or six criteria. A score is the weighted share of criteria met. Method, criteria and caveats: [evals/](evals/README.md).

<table>
  <thead>
    <tr>
      <th rowspan="2" align="left">Case</th>
      <th colspan="2">Sonnet</th>
      <th colspan="2">Opus</th>
    </tr>
    <tr>
      <th align="right">without</th><th align="right">with bluML</th>
      <th align="right">without</th><th align="right">with bluML</th>
    </tr>
  </thead>
  <tbody>
    <tr><td><code>fraud-threshold</code></td><td align="right">0.52</td><td align="right"><b>1.00</b></td><td align="right">0.63</td><td align="right"><b>0.96</b></td></tr>
    <tr><td><code>design-doc</code></td><td align="right">0.59</td><td align="right"><b>1.00</b></td><td align="right">0.93</td><td align="right"><b>1.00</b></td></tr>
    <tr><td><code>ctr-drop</code></td><td align="right">0.58</td><td align="right"><b>0.96</b></td><td align="right">0.88</td><td align="right"><b>0.96</b></td></tr>
    <tr><td><code>rule-first</code></td><td align="right">0.25</td><td align="right"><b>0.58</b></td><td align="right">0.50</td><td align="right"><b>0.83</b></td></tr>
    <tr><td><code>ship-it</code></td><td align="right">0.88</td><td align="right"><b>1.00</b></td><td align="right">0.96</td><td align="right"><b>1.00</b></td></tr>
    <tr><td><code>churn-leak</code></td><td align="right">0.92</td><td align="right"><b>1.00</b></td><td align="right">1.00</td><td align="right">1.00</td></tr>
    <tr><td><code>ranker-clicks</code></td><td align="right"><b>0.96</b></td><td align="right">0.92</td><td align="right">1.00</td><td align="right">1.00</td></tr>
    <tr><td><b>Mean</b></td><td align="right"><b>0.67</b></td><td align="right"><b>0.92</b></td><td align="right"><b>0.84</b></td><td align="right"><b>0.96</b></td></tr>
  </tbody>
</table>

Without bluML, both models already catch the textbook traps: a backfilled column, position bias in clicks, prices sent in cents. What they skip is the product reasoning around the model. Neither compared the fraud model with the rule slice by slice, and neither noticed that it ranks new customers far worse (0 of 6 runs; 6 of 6 with bluML). Sonnet never scored the keyword rule on the same held-out tickets as its ticket-routing model (0 of 3; 3 of 3), Opus seldom weighed the model against that rule, which nearly matches it (1 of 3; 3 of 3), and none of Sonnet's design docs set out a product metric, guardrails and an online test (0 of 3; 3 of 3). One gap remains: Sonnet with bluML still seldom weighs the model's small gain over the rule against the cost of running it (1 of 3), and never prices a misrouted ticket.

</details>

## Install

As a Claude Code plugin:

```text
/plugin install bluml --marketplace 0trm/bluml
```

Or copy the skills into a project:

```bash
git clone https://github.com/0trm/bluml
mkdir -p .claude/skills
cp -r bluml/skills/* .claude/skills/
```

The scripts need Python 3.10 or later with numpy and pandas; `uv run <script>` installs them. Run their tests with `uv run --with numpy,pandas,pytest pytest tests`.

## Scope

bluML covers supervised models that run inside a product: a classifier, a ranker or a forecast whose output the product acts on. LLM applications, research, ML platform work and unsupervised models are out of scope. What each skill is written from, and where its sources disagree: [docs/sources.md](docs/sources.md).

## License

[MIT](LICENSE) for text and code. Painting by Ono Chikkyō (小野竹喬, 1889–1979), *For Haiku Poems in Bashō's Narrow Road to a Far Province*.
