---
name: exploring-data
description: "Looks at a product model's data before anything is designed or built, and puts it in front of the model's owner without asking them to read code. Covers five sections for any model: the grain and completeness of the rows, the target over time with its steps and seasonality, the target's shape and sparsity, the segments and outliers that carry the volume, and the spread that sets the loss and the interval width. Builds one JupyterLab notebook, eda.ipynb beside MODEL.md, where each section shows a question and a chart with its code folded away, asks the owner to write what they see before opening the agent's folded reading, states what it means for the model and records any decision; the owner's readings come back in the notebook itself. Use after framing names the decision and before the design doc, when someone asks to explore, profile or look at the data or asks for EDA, and again when a source or the tracking changes."
---

# Exploring data

A model is only as honest as its owner's picture of the data, and that picture comes from looking, not from summary numbers. An agent can draw every chart in seconds; what it cannot do is make the owner understand them. Build the look so that the person who answers for the model reads each chart and writes what they see before the agent says what it sees.

Read the model's `MODEL.md` first. The Decision section names the unit, the moment of prediction and the slices the decision is judged on, and the exploration follows them. If there is no Decision section, run `framing-models` first: data explored before the decision is framed answers questions nobody asked.

Run it after framing and before the design doc, whose feasibility numbers come from here (`writing-design-docs` step 2). Run it again when a source changes or the tracking does.

Copy this checklist into your work and tick it as you go:

```
- [ ] 1. Scope and slices taken from MODEL.md
- [ ] 2. eda.ipynb started from the template beside MODEL.md
- [ ] 3. Five sections drawn and run: grain, time, target, segments, uncertainty
- [ ] 4. Agent's readings written and folded, outputs aggregates only, notebook handed to the owner
- [ ] 5. Owner's readings and decisions read back, disagreements looked at again
- [ ] 6. MODEL.md Data section: path, decisions, gate
```

## 1. Take the scope from the decision

Write down, from `MODEL.md`: the unit one row stands for, the window, the filters that define the population, the target, and the slices the decision is judged on (a market, a page, a customer type). Use the filters the model will use. Exploring a different population describes a different model.

## 2. Start the notebook from the template

Copy [templates/eda.ipynb](templates/eda.ipynb) to `eda.ipynb` next to `MODEL.md` and fill its header with the scope from step 1. Its setup cell reads the extract the training table will come from; each of the five sections below it has a question, a chart cell, a box for the owner, the agent's reading and, where one is needed, a decision.

The code is the evidence behind every chart and stays in the notebook, each chart under the code that drew it, but it is folded away: the owner reads charts, not code, and a reviewer opens a cell to check one. Keep the template's cell tags (`question`, `chart`, `owner-reading`, `agent-reading`, `decision`) and its folding (`"jupyter": {"source_hidden": true}` in a cell's metadata): reading the notes back depends on the tags, and the order the owner reads in depends on the folding.

## 3. Draw the five sections

The same five for any model. Each answers one question with one or two charts and the counts behind them.

1. **Grain and completeness.** What one row is, how many rows each filter removes, missing values per column, and the first and last non-empty day of each column. A column that starts mid-window cannot be a feature across the whole history.
2. **Time.** The level and trend of the target, steps at dated changes (a release, a tracking fix, a price change), the weekly or seasonal pattern, and partial periods at either end. Mark every known change on the chart: a step that lines up with a release is the release, not the users.
3. **The target.** Its distribution: the share of zeros, the skew, the tail. Its sparsity: how many rows each entity the model will score actually has. Its split by each slice the decision uses. A target that is mostly zeros, or entities with a handful of rows, settle the grain and the loss before any model is chosen.
4. **Segments and concentration.** Which entities carry the volume, and the outliers: entities, sessions or days above the third quartile plus 1.5 times the interquartile range, with the share of the total each explains. One segment with most of the volume makes every pooled number that segment's number.
5. **Uncertainty.** For counts, the variance against the mean per entity: far above the mean, a Poisson range is too narrow. For anything else, the spread by segment. This sets the loss (a quantile when the two errors cost differently, `framing-models` step 2) and how wide an interval must be.

Every chart names its unit and its real window in the title, gives rates under about 30 their count, and shows groups apart when a rule, a size or a period differs between them.

Run the notebook end to end, so that the saved outputs are the charts the owner reads:

```bash
jupyter nbconvert --to notebook --execute --inplace eda.ipynb
```

Outputs are saved in the file and travel with it. Print counts and draw charts; never show rows (`df.head()`, a sample) or row-level identifiers (user, session, customer or account ids).

## 4. Write the readings and hand it over

Each section reads, top to bottom:

- **The question,** in the product's words.
- **The chart,** with the counts it rests on printed under it.
- **The owner's box:** a Markdown cell the owner fills before opening anything below it. Writing a reading before seeing one is how it sticks, and it is the only way to tell that the owner understood the chart rather than agreed with the agent.
- **The agent's reading,** in a folded cell under the box, written before the owner opens the notebook. Evidence first (what the chart shows, with numbers), then inference, labelled as such, then what it means for the model: the grain, the window, a feature to drop, the loss, the interval.
- **A decision,** where one is needed: a cap, a period to drop, a window to train on, a slice to model apart. Write the question and its options; the owner writes the choice.

Fold the agent's reading before handing the notebook over. The fold asks the owner to write first; it cannot stop them opening the reading, which is why the reading back checks for it.

Tell the owner to open it with `jupyter lab eda.ipynb` (`uvx --from jupyterlab jupyter lab eda.ipynb` where JupyterLab is not installed). Reading needs no kernel and no access to the data: the charts are in the file. The owner writes in each box (double-click, then Shift+Enter), opens the folded reading, takes any decision and saves.

Follow-up questions can go to Claude inside JupyterLab, once the owner has written their reading and opened the agent's: asked first, Claude answers before the owner has looked. Jupyter AI runs Claude Code in JupyterLab's chat panel: `pip install jupyter-ai` where JupyterLab runs, `npm install -g @agentclientprotocol/claude-agent-acp` for the bridge, then pick Claude in the chat's persona menu. It reads the notebook with its saved charts. A question that needs new numbers makes it add and run a cell, which needs the kernel and the data; it may put the cell anywhere in the notebook, untagged and unsaved. Delete such cells, or move the ones worth keeping below the last section, before saving.

## 5. Read the owner's notes back

When the owner says they are done, read the cells tagged `owner-reading` and `decision` from `eda.ipynb`. A box that still holds the template's placeholder has no reading; an `agent-reading` cell saved unfolded above an empty box means the owner read the agent's reading before writing their own. Where the owner's reading and the agent's disagree, say so and look again: one of them missed something. A decision taken in the notebook applies to every later step that uses the data.

When a source or the tracking changes, run the notebook again. The owner's text survives a run, so clear the box, the reading and the decision of every section whose chart changed, fold the new reading and hand it over again.

## Write it down

Fill the Exploration bullet at the top of the Data section of `MODEL.md`, although exploration runs before the design: the path to `eda.ipynb` and one line per decision it led to, each with its evidence. Tick the exploration gate item if every section has the owner's reading and an implication, and add a dated line to the log. If a section has no owner's reading, leave the item unticked and say which.

## Report

Lead with what the data allows, in one line: the grain, the window and the loss it points to. Then the decisions taken in the notebook, and the sections where the owner's reading and the agent's differed.

## Stop signs

- Exploring before the decision is framed.
- A section whose only reading is the agent's.
- An agent's reading left unfolded when the notebook is handed over.
- Rows or row-level identifiers in a saved output.
- A summary number with no chart behind it.
- A decision taken from a chart nobody looked at.
- A notebook run on a different population than the model will see.
