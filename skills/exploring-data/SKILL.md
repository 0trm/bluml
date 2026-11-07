---
name: exploring-data
description: "Looks at a product model's data before anything is designed or built, and puts it in front of the model's owner without asking them to read code. Covers five sections for any model: the grain and completeness of the rows, the target over time with its steps and seasonality, the target's shape and sparsity, the segments and outliers that carry the volume, and the spread that sets the loss and the interval width. Builds one page where each section shows a question and a chart, asks the owner what they see before revealing the agent's reading, states what it means for the model and records any decision; the code stays in eda.py beside MODEL.md. Use after framing names the decision and before the design doc, when someone asks to explore, profile or look at the data or asks for EDA, and again when a source or the tracking changes."
---

# Exploring data

A model is only as honest as its owner's picture of the data, and that picture comes from looking, not from summary numbers. An agent can draw every chart in seconds; what it cannot do is make the owner understand them. Build the look so that the person who answers for the model reads each chart and writes what they see before the agent says what it sees.

Read the model's `MODEL.md` first. The Decision section names the unit, the moment of prediction and the slices the decision is judged on, and the exploration follows them. If there is no Decision section, run `framing-models` first: data explored before the decision is framed answers questions nobody asked.

Run it after framing and before the design doc, whose feasibility numbers come from here (`writing-design-docs` step 2). Run it again when a source changes or the tracking does.

Copy this checklist into your work and tick it as you go:

```
- [ ] 1. Scope and slices taken from MODEL.md
- [ ] 2. eda.py written and run beside MODEL.md
- [ ] 3. Five sections drawn: grain, time, target, segments, uncertainty
- [ ] 4. Page built: aggregates only, code hidden, owner's reading before the agent's
- [ ] 5. Owner's notes read back, disagreements looked at again
- [ ] 6. MODEL.md Data section: link, decisions, gate
```

## 1. Take the scope from the decision

Write down, from `MODEL.md`: the unit one row stands for, the window, the filters that define the population, the target, and the slices the decision is judged on (a market, a page, a customer type). Use the filters the model will use. Exploring a different population describes a different model.

## 2. Write the code once, beside the record

Put the code in `eda.py` next to `MODEL.md`, one block per section, reading the same extract the training table will come from. Run it end to end; the page is built from its output. The code is the evidence behind every chart and stays in the repository, but it never appears on the page: the owner reads charts, not code.

## 3. Draw the five sections

The same five for any model. Each answers one question with one or two charts and the counts behind them.

1. **Grain and completeness.** What one row is, how many rows each filter removes, missing values per column, and the first and last non-empty day of each column. A column that starts mid-window cannot be a feature across the whole history.
2. **Time.** The level and trend of the target, steps at dated changes (a release, a tracking fix, a price change), the weekly or seasonal pattern, and partial periods at either end. Mark every known change on the chart: a step that lines up with a release is the release, not the users.
3. **The target.** Its distribution: the share of zeros, the skew, the tail. Its sparsity: how many rows each entity the model will score actually has. Its split by each slice the decision uses. A target that is mostly zeros, or entities with a handful of rows, settle the grain and the loss before any model is chosen.
4. **Segments and concentration.** Which entities carry the volume, and the outliers: entities, sessions or days above the third quartile plus 1.5 times the interquartile range, with the share of the total each explains. One segment with most of the volume makes every pooled number that segment's number.
5. **Uncertainty.** For counts, the variance against the mean per entity: far above the mean, a Poisson range is too narrow. For anything else, the spread by segment. This sets the loss (a quantile when the two errors cost differently, `framing-models` step 2) and how wide an interval must be.

Every chart names its unit and its real window in the title, gives rates under about 30 their count, and shows groups apart when a rule, a size or a period differs between them.

## 4. Build the page

One page, the sections in the order above. Each section has:

- **The question,** in the product's words.
- **The chart,** with the counts it rests on.
- **What do you see?** A box the owner fills in before anything else in the section is shown. Writing a reading before seeing one is how it sticks, and it is the only way to tell that the owner understood the chart rather than agreed with the agent.
- **The agent's reading,** revealed once the box has text or the owner chooses to skip. Evidence first (what the chart shows, with numbers), then inference, labelled as such.
- **What it means for the model:** the grain, the window, a feature to drop, the loss, the interval.
- **A decision,** where one is needed: a cap, a period to drop, a window to train on, a slice to model apart. The owner takes it on the page.

Aggregates only: no row-level identifiers (user, session, customer or account ids) on the page, which may travel further than the data was meant to.

Publish it:

- **As a Claude Code Artifact** when the agent can publish one. It is private by default; the notes and decisions are saved in the page's database, so the agent reads them back instead of asking for them.
- **Otherwise as one HTML file** from [templates/EDA.html](templates/EDA.html), beside `MODEL.md`. It keeps the owner's notes in the browser and has a "Copy notes as Markdown" button; the owner pastes the result back to the agent.

Both follow the same template: the Artifact swaps the browser's storage for the page's database.

## 5. Read the owner's notes back

When every section has the owner's reading, read the notes and decisions, from the page's database or the pasted Markdown. Where the owner's reading and the agent's disagree, say so and look again: one of them missed something. A decision taken on the page applies to every later step that uses the data.

## Write it down

Fill the Exploration bullet at the top of the Data section of `MODEL.md`, although exploration runs before the design: the link to the page and one line per decision it led to, each with its evidence. Tick the exploration gate item if every section has the owner's reading and an implication, and add a dated line to the log. If a section has no owner's reading, leave the item unticked and say which.

## Report

Lead with what the data allows, in one line: the grain, the window and the loss it points to. Then the decisions taken on the page, and the sections where the owner's reading and the agent's differed.

## Stop signs

- Exploring before the decision is framed.
- A section whose only reading is the agent's.
- Row-level identifiers on the page.
- A summary number with no chart behind it.
- A decision taken from a chart nobody looked at.
- A page built from a different population than the model will see.
