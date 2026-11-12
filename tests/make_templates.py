# %%
"""Write the skills' four owner notebooks (eda, data, train, eval) from one section layout.

    python3 tests/make_templates.py

Every section reads question, chart, the owner's box, the agent's folded reading and, where
the section ends in one, the decision; the owner's pick comes before the recommendation.
Change a notebook here and run this file: tests/test_templates.py fails when a template
differs from what this writes, so a hand edit to one notebook cannot drift from the others.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS: dict[str, dict] = {}

HIDDEN = {"jupyter": {"source_hidden": True}}

READ_PLAIN = "_What do you see? Double-click here, write it, then press Shift+Enter._"
READ_PICK = ("_What do you see, which option do you pick, and why? Double-click here, write both, "
             "then press Shift+Enter. Write them before you open the folded reading below._")
DECIDED = ("**Decided, in your words:** _after reading both, double-click, write the option you take "
           "and why, then press Shift+Enter._")


def lines(text: str) -> list[str]:
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + [parts[-1]]


def md(cid: str, text: str, tag: str, hidden: bool = False) -> dict:
    meta = dict(HIDDEN) if hidden else {}
    meta["tags"] = [tag]
    return {"cell_type": "markdown", "id": cid, "metadata": meta, "source": lines(text)}


def code(cid: str, text: str, tag: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "id": cid,
            "metadata": {**HIDDEN, "tags": [tag]}, "outputs": [], "source": lines(text)}


def section(n: int, slug: str, title: str, question: str, charts: list, means: str,
            decision: tuple | None = None, extra: tuple | None = None) -> list[dict]:
    """One section: question, optional markdown cell (cards, groups), charts, owner box,
    the agent's folded reading (with its recommendation when there is a decision), decision."""
    q = f"## {n}. {title}\n\n**{question}**\n\n"
    under = "chart" if charts else "table"
    if decision:
        what, options, rule = decision
        q += f"**Decision:** {what} Options: {options}."
        q += f" Rule: {rule}\n\n" if rule else "\n\n"
        q += (f"Write what you see, and the option you pick, in the box under the {under} before you open "
              "the folded reading below it.")
    else:
        q += f"Write what you see in the box under the {under} before you open the folded reading below it."
    cells = [md(f"{slug}-question", q, "question")]
    if extra:
        tag, text = extra
        cells.append(md(f"{slug}-{tag}", text, tag))
    for i, body in enumerate(charts):
        suffix = "" if len(charts) == 1 else f"-{'abc'[i]}"
        cells.append(code(f"{slug}-chart{suffix}", body, "chart"))
    cells.append(md(f"{slug}-owner-reading", READ_PICK if decision else READ_PLAIN, "owner-reading"))
    reading = (f"### The agent's reading\n\n- {{Evidence: what the {under} shows, with numbers.}}\n\n"
               "*Inference:* {what it likely means, labelled as such}\n\n"
               f"### What it means for the model\n\n{means}")
    if decision:
        reading += ("\n\n### Recommendation\n\n{The option, and the evidence that picks it"
                    + (" under the rule.}" if decision[2] else ".}"))
    cells.append(md(f"{slug}-agent-reading", reading, "agent-reading", hidden=True))
    if decision:
        cells.append(md(f"{slug}-decision", DECIDED, "decision"))
    return cells


def chart(n: str, title: str, body: str, step: str | None = None) -> str:
    log = f'\n# log_charts("{step}", {{"<name>": fig}}) in the run this chart comes from.' if step else ""
    return (f"# {n}. {title}: {{what this cell computes}}\n"
            "# Aggregates only: print counts and draw charts, never rows or row-level ids.\n"
            f"# {{code: {body}, then the counts the chart rests on}}{log}")


HOW = ("**How to read it.** Each section asks a question and shows a chart. Write what you see in the box "
       "under it and, where the section names a decision, the option you pick. Then click the folded "
       "cell below the box to open the agent's reading and its recommendation, and write the decision last, "
       "in your words. The code behind each chart is folded too; click it if you want to see it. Save when "
       "you are done (Cmd+S or Ctrl+S): the agent reads your notes from this file.")
STEPWISE = (" The agent fills one section per step and waits for your go before the next, so the sections "
            "below the current one are still empty.")
FOOT_STEP = ("When this step's box and decision are written, save the notebook and tell the agent to go on. "
             "It reads your reading and decision from this file, records the decision in MODEL.md, says where "
             "its reading and yours differ, and starts the next step only on your go.")


def notebook(cells: list[dict]) -> dict:
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                                        "name": "python3"}, "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


def add(rel: str, cells: list[dict]) -> None:
    NOTEBOOKS[rel] = notebook(cells)


def render(rel: str) -> str:
    """The file's text, exactly as written."""
    return json.dumps(NOTEBOOKS[rel], indent=1, ensure_ascii=False) + "\n"


# %% eda.ipynb: exploring-data
eda = [md("header", "# {model name}: what the data looks like\n\n"
          "{The decision in one line, from MODEL.md: what the product does with each prediction.}\n\n"
          "Scope: {unit of one row}, {window, first to last non-empty day}, {filters}. Slices: {the slices the "
          "decision is judged on}. Record: [MODEL.md](MODEL.md). Run {YYYY-MM-DD}.\n\n" + HOW, "header"),
       code("setup", "# Setup: read the extract the training table will come from, with the filters from MODEL.md.\n"
            "import pandas as pd\nimport matplotlib.pyplot as plt\n\n"
            'rows = pd.read_parquet("{extract}")  # {filters}', "setup")]
eda += section(1, "grain", "Grain and completeness",
               "{What is one row, how many rows does each filter remove, and which columns are empty for part of the window?}",
               [chart("1", "Grain and completeness", "rows removed by each filter, missing values per column, first and last non-empty day of each column")],
               "{The grain, the window or the feature it settles.}")
eda += section(2, "time", "Time",
               "{How does the target move over the window, and do its steps line up with dated changes?}",
               [chart("2", "Time", "the target by day or week, every known change marked and labelled, partial periods named")],
               "{The window to train on, the breaks to mark.}",
               decision=("{The decision, e.g. which window to train on.}", "{option A}; {option B}",
                         "{how to choose, e.g. the longest window with no step the model cannot explain}."))
eda += section(3, "target", "The target",
               "{How is the target distributed, how many rows does each entity have, and how does it split by the decision's slices?}",
               [chart("3", "The target", "the share of zeros, the skew and the tail; rows per entity; the target by each slice")],
               "{The grain and the loss it points to.}")
eda += section(4, "segments", "Segments and concentration",
               "{Which entities carry the volume, and which entities, sessions or days are outliers (above Q3 + 1.5 IQR)?}",
               [chart("4", "Segments and concentration", "the volume by entity, the outliers and each one's share of the total")],
               "{Caps, drops or slices to model apart.}",
               decision=("{The decision, e.g. a cap per session.}", "{option A}; {option B}",
                         "{how to choose, e.g. the cap that removes the outliers' share without touching the slices}."))
eda += section(5, "uncertainty", "Uncertainty",
               "{How much does the target vary beyond its mean, and how wide must a range be?}",
               [chart("5", "Uncertainty", "variance against mean per entity for counts, spread by segment otherwise")],
               "{The loss and the interval width.}")
eda.append(md("footer", "When every box has your reading, and every decision your pick and your decision, save the "
              "notebook and tell the agent. It reads your readings and decisions from this file and comes back where "
              "its reading and yours differ.", "footer"))
add("skills/exploring-data/templates/eda.ipynb", eda)

# %% data.ipynb: building-datasets
data = [md("header", "# {model name}: the training table\n\n"
           "{The decision in one line, from MODEL.md: what the product does with each prediction.}\n\n"
           "Table: {path}, one row per {entity} per prediction time, {first to last prediction time}. Label: {the "
           "event and its window}. Split: {train, validation and test windows}. Record: [MODEL.md](MODEL.md). "
           "Exploration: [eda.ipynb](eda.ipynb). Run {YYYY-MM-DD}.\n\n" + HOW, "header"),
        code("setup", "# Setup: read the built training table, and the leak screen from building-datasets.\n"
             "import importlib.util\n\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\n"
             'table = pd.read_parquet("{training table}")  # one row per {entity} per prediction time\n'
             'LABEL, TIME, ID, SPLIT = "{label}", "{prediction time}", "{entity id}", "{split}"\n'
             'ORIGIN = {"{feature}": "{source table or service}"}  # every feature, by where its value comes from\n\n'
             'spec = importlib.util.spec_from_file_location("leakage_screen", "{full path to building-datasets/scripts/leakage_screen.py}")\n'
             "leakage_screen = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(leakage_screen)", "setup")]
data += section(1, "label", "The label, the rows and the split",
                "{How often does the label happen, how does its rate move over prediction time, and do the latest rows, whose window has not closed, dip?}",
                [chart("1", "The label", "the label rate by week of prediction time, with the split boundaries and the rows whose label window is still open marked; rows, positives and the rate per split")],
                "{The rows, the label window and the split.}",
                decision=("{The rows, the label and the split: which rows train, validate and test, and what happens to the rows whose label window is still open.}",
                          "{option A, e.g. train to May, validate June, test July, drop the last 14 days}; {option B}",
                          "{how to choose, e.g. the split that mirrors serving, with a gap as long as the label window}."))
data += section(2, "features", "Each feature by origin and split",
                "{Where does each feature's value come from, and does it look the same in train, validation and test?}",
                [chart("2", "Features by origin and split", "the features grouped by ORIGIN; per feature and split, the missing rate and the quartiles, one small panel per feature, a feature that shifts between splits marked")],
                "{Features whose value or missing rate changes between splits, and what serving will see.}")
data += section(3, "leaks", "The leak screen",
                "{Which features are strong enough alone, or change strength over time, to be leaks until their source and timestamp explain them?}",
                ["# 3. The leak screen: each feature's strength alone, overall and by stretch of time.\n"
                 "# Aggregates only: print counts and draw charts, never rows or row-level ids.\n"
                 "result = leakage_screen.screen(table, LABEL, time=TIME, id_col=ID, split=SPLIT)\n"
                 '# {code: a bar per feature for its strength alone, with the too-strong line (AUC 0.90, or |rho| 0.80 for a numeric label); a line per flagged feature across result["stretches"]; then print result["flags"]}'],
                "{The features that stay out, and the flags their source explains.}",
                decision=("{Which flagged features stay out of training.}",
                          "drop it; keep it, with the explanation from its source and timestamp",
                          "a flagged feature stays out until its source and timestamp explain the flag."))
data.append(md("footer", "When every box has your reading, and every decision your pick and your decision, save the "
               "notebook and tell the agent. It reads them from this file, records the rows, the label and the split "
               "in MODEL.md, and starts training only on your go.", "footer"))
add("skills/building-datasets/templates/data.ipynb", data)

# %% train.ipynb: training-models
train = [md("header", "# {model name}: training\n\n"
            "{The decision in one line, from MODEL.md: what the product does with each prediction.}\n\n"
            "Table: {path and data version}. Validation: {window}. Operating point: {threshold, top k or quantile}. "
            "The rule to beat: {its number at the operating point}. Break-even gain: {from the case}. MLflow "
            "experiment: {name}. Record: [MODEL.md](MODEL.md). Run {YYYY-MM-DD}.\n\n" + HOW + STEPWISE, "header"),
         code("setup", "# Setup: the training table, its split, and the run log. The test window is never read here.\n"
              "import mlflow\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\n"
              'table = pd.read_parquet("{training table}")\n'
              'train, valid = table[table["{split}"] == "train"], table[table["{split}"] == "valid"]\n'
              'OPERATING_POINT = "{threshold, top k or quantile, from the Decision section}"\n\n'
              'mlflow.set_experiment("{model name}")\n\n\n'
              "def log_charts(step: str, charts: dict) -> None:\n"
              '    """Tag the active run with its step and log each chart, so the MLflow UI shows the evidence."""\n'
              '    mlflow.set_tag("step", step)\n'
              "    for name, fig in charts.items():\n"
              '        mlflow.log_figure(fig, f"charts/{step}/{name}.png")', "setup")]
train += section(1, "candidates", "The candidates and the comparison rule",
                 "{Which models are worth fitting, and what rule decides between them?}",
                 [], "{The candidates worth fitting, and the rule they will be judged by.}",
                 decision=("{The comparison rule and its tie-break, written before any fit.}",
                           "{e.g. the best {metric} at the operating point wins when it beats the next by more than the spread between folds, and the simpler model wins a tie}; {another rule}",
                           None),
                 extra=("cards", "| Candidate | Its assumption | Serving cost | How it fails |\n|---|---|---|---|\n"
                        "| {the simple model, e.g. logistic regression on a handful of features} | {what must hold in the data for it to win} | {latency, compute, upkeep} | {what it gets wrong first} |\n"
                        "| {e.g. gradient-boosted trees} | {...} | {...} | {...} |\n\n"
                        "Baselines every candidate must beat: {the trivial baseline}; {the rule}; {the simple model}."))
train += section(2, "baselines", "Baselines",
                 "{How do the trivial baseline, the rule and the simple model score at the operating point on the validation rows?}",
                 [chart("2", "Baselines", "each baseline at the operating point on the validation rows, with the spread between folds as error bars", "baselines")],
                 "{The bar every candidate must clear, and whether the pipeline holds.}",
                 decision=("{Fit the candidates, or fix the pipeline first.}",
                           "go on; fix the label, the features or the join",
                           "the simple model beats the trivial baseline by more than the spread between folds."))
train += section(3, "debug", "Debugging and the ceiling",
                 "{Does the model learn, and how high can these features go?}",
                 [chart("3", "Debugging and the ceiling", "training and validation loss by iteration; the ceiling, scored on the model's own training rows, against the rule plus the break-even gain; the learning curve on a quarter, half and all of the rows", "debug")],
                 "{Whether these features can clear the break-even gain, and whether more data will help.}",
                 decision=("{Go on to the features, or change what the model sees.}",
                           "go on; new signal or a new framing; more data",
                           "{the ceiling against the rule plus the break-even gain, and the slope of the learning curve}."))
train += section(4, "groups", "Feature groups and the keep rule",
                 "{Which groups of features are worth trying, and what rule keeps a group?}",
                 [], "{The groups to run, in order, and the rule that keeps them.}",
                 decision=("{The keep rule, written before any feature run.}",
                           "{e.g. keep a group whose gain at the operating point beats the spread between folds}; {e.g. a gain above twice the spread that also pays its upkeep}",
                           None),
                 extra=("groups", "| Group | What it says about the {entity} | Features | Why it is tried |\n|---|---|---|---|\n"
                        "| {e.g. account history} | {...} | {columns} | {the idea it tests} |"))
train += section(5, "features", "The feature runs",
                 "{Which groups earn their place under the keep rule, and which columns repeat another?}",
                 [chart("5a", "Gain per group", "one panel per measure ({metric at the operating point}, {a threshold-free measure}), each group's gain against the spread between folds", "features"),
                  chart("5b", "Ablation", "what removing each kept group costs at the operating point, with the spread between folds", "features"),
                  chart("5c", "Near-duplicates", "the rank correlation between features as a heatmap, pairs above 0.9 marked", "features")],
                 "{The kept groups with what removing each costs; each dropped near-duplicate beside the column it repeats and the one that stayed; a draft Why in line for each kept feature.}",
                 decision=("{The kept groups, each dropped near-duplicate, and each Why in line.}",
                           "{the groups the keep rule keeps}; {another set, with why}",
                           "the keep rule from section 4."))
train += section(6, "tuning", "Tuning",
                 "{Which settings matter, and when do more trials stop paying?}",
                 [chart("6", "Tuning", "each trial's validation result at the operating point against the settings searched, with the spread between folds as a band", "tuning")],
                 "{The settings to keep, and whether more search can help.}",
                 decision=("{The trial to keep, or stop tuning.}",
                           "{the best trial}; {a simpler trial within the spread between folds}",
                           "the comparison rule from section 1."))
train += section(7, "choice", "The choice",
                 "{Which model beats the rule by enough to be worth running?}",
                 [chart("7", "The choice", "every baseline and candidate at the operating point on the same validation rows, with the spread between folds, the rule and the break-even line; the reliability chart when the decision uses the probability", "choice")],
                 "{The model to hand to evaluation, and what it costs to run.}",
                 decision=("{The chosen model.}", "{a candidate}; {the simple model}; the rule ships",
                           "the comparison rule and tie-break from section 1."))
train.append(md("footer", FOOT_STEP, "footer"))
add("skills/training-models/templates/train.ipynb", train)

# %% eval.ipynb: evaluating-models
ev = [md("header", "# {model name}: evaluation\n\n"
         "{The decision in one line, from MODEL.md: what the product does with each prediction.}\n\n"
         "Chosen model: {run id}. Validation: {window}. Test window: {window}, closed until section 5. The rule: "
         "{its number}. Break-even gain: {from the case}. Threshold owner: {who}. Record: [MODEL.md](MODEL.md). "
         "Training: [train.ipynb](train.ipynb). Run {YYYY-MM-DD}.\n\n" + HOW + STEPWISE, "header"),
      code("setup", "# Setup: validation rows scored by the chosen model and the rule. The test window stays closed until section 5.\n"
           "import pandas as pd\nimport matplotlib.pyplot as plt\n\n"
           'valid = pd.read_parquet("{validation rows with the model\'s and the rule\'s scores}")', "setup")]
ev += section(1, "point", "The operating point",
              "{Where should the product act, given what each error costs or the capacity it has?}",
              [chart("1", "The operating point", "the total cost, or the metric being optimized, by threshold on validation, the range that costs about the same shaded, the rule marked; the calibration table")],
              "{The operating point, the range around it, and who must agree to it.}",
              decision=("{The operating point, agreed with the threshold owner.}",
                        "{the lowest-cost threshold}; {a threshold inside the range that costs about the same, for workload}",
                        "{the lowest total cost on validation, or the best {metric} above the floor}."))
ev += section(2, "rule", "Against the rule",
              "{How much better does the model decide than the rule, in the decision's unit, at their operating points?}",
              [chart("2", "Against the rule", "the paired difference, model minus rule, on the validation rows in the decision's unit, with its interval")],
              "{The gain the test run will check.}")
ev += section(3, "slices", "Slices",
              "{Where does the model lose to the rule, and which slices are too small to judge?}",
              [chart("3", "Slices", "the difference by slice with its interval, rows and positives per slice, slices under about 30 positives marked too small to judge")],
              "{Each slice where the model loses, and what it needs.}",
              decision=("{The policy for each slice where the model loses.}",
                        "keep the rule there; a separate threshold; a separate model; more data for that slice",
                        "no slice that matters does worse than the rule without its own policy."))
ev += section(4, "errors", "Errors left",
              "{Which errors are left, and is their fix data or the model?}",
              [chart("4", "Errors left", "the tagged errors, both kinds, counted by cause, each with its distance from the best achievable")],
              "{The next fix, and what it should move.}",
              decision=("{The next fix.}", "{more examples of a slice}; {cleaner labels}; {a new signal}; {the model}",
                        "the largest share of errors times its distance from the best achievable."))
ev += section(5, "test", "The test run",
              "{With every choice above decided, what does the test window say, scored once?}",
              [chart("5", "The test run", "the model against the rule on the test window, once, in the decision's unit, with its interval; the date and the count of test runs printed")],
              "{Whether the gain holds on rows no choice has seen.}")
ev += section(6, "verdict", "The verdict",
              "{Does the measured gain pay for the model?}",
              [chart("6", "The verdict", "net value per month at the measured gain and at both ends of its interval, against the break-even gain")],
              "{The verdict, and what would change it.}",
              decision=("{The verdict.}", "ready for launch; ship the rule while labels accumulate; back to training or data, with the condition that fails",
                        "the conditions in evaluating-models step 6."))
ev.append(md("footer", FOOT_STEP, "footer"))
add("skills/evaluating-models/templates/eval.ipynb", ev)


# %%
if __name__ == "__main__":
    for rel in NOTEBOOKS:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(rel))
        print("wrote", rel, len(NOTEBOOKS[rel]["cells"]), "cells")
