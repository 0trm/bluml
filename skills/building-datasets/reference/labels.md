# Labels

A model learns what its labels say, so the labels cap what it can do. This file covers where labels come from, how to make people label consistently, how to grow a small set, labels that change after they are recorded, the negatives a ranker learns from, and the set kept back for evaluation.

## Contents

- Where labels come from
- Guidelines for people who label
- Agreement
- Growing a small set
- Labels the product already has
- Labels that change after they are recorded
- Negatives for rankers and retrieval
- A set checked by hand, for evaluation

## Where labels come from

| Source | Examples | What it brings in |
|---|---|---|
| Users | Spam flags, harassment reports, disputed charges confirmed as fraud | Labels only for what users saw and chose to report; blocking a sender is a weaker signal than a report |
| Existing systems | A table's classification passed on to the tables built from it; code paths that only ever handle one kind of data | Labels at no cost, as good as the system that wrote them |
| Annotators | An internal team, a vendor or experts labelling a sample | The ambiguous cases rules miss, and new patterns; slow and costly, so it becomes the bottleneck |
| Rules that are right when they fire | Rules that settle the cases they are sure of, such as bot rules that classify 15% of traffic with the lowest false positive rate of any method | Many labels, but only for the cases the rule recognizes; a model trained only on them learns the rule |

No single source is enough. Most programs start from user reports or annotators, then grow that seed with the methods below.

## Guidelines for people who label

A clear guideline does more for consistency than more votes per item. It answers five questions:

1. **Why the task matters:** the product feature the labels power, with a screenshot. People who see the purpose take the care it needs.
2. **What the task is:** what to look at, from the user's point of view, split into small steps, with the label options shown early.
3. **What the terms mean:** every term, even the ones that seem obvious, and any word the product coined.
4. **How to decide:** the factors to weigh, a decision tree, and worked hard cases with the right label and the reason. This is most of the guideline.
5. **How to work:** time per item, what to do when two labels fit or none does, and an "unsure" option, which beats a forced guess.

Ask binary questions where possible: they are faster and more precise than scales. Make criteria objective: "does the image show nudity?" gets more consistent answers than "is this adult content?". When labels are tags, make them mutually exclusive, split the top level by independent attributes (cuisine, flavour) so each can be labelled apart, and keep an "other" tag at every level to revisit later. Avoid tags that change with time or taste ("popular").

## Agreement

Have two people label the same items and measure their agreement beyond chance (Cohen's kappa). Low agreement caps any model trained on the labels: report it as the ceiling in error analysis (`evaluating-models`). When the guideline changes, agreement should hold or rise; if it falls, the change made the task less clear.

Check the labellers as well as the guideline: mix items with known labels into each new labeller's queue to measure their precision before their labels count, ask for more votes only on the classes where labellers often disagree, and compare vendors on the same items to catch a systematic lean.

## Growing a small set

From a seed checked by hand:

| Method | How | Fits |
|---|---|---|
| Weak supervision | Write heuristics (keywords, thresholds, lookups in existing data) as labelling functions that return a label or abstain; a label model weighs each by where they agree and disagree, and combines them into noisy, plentiful labels | Early, with almost no labels |
| Active learning | Send people the items that would teach the model most: those it is least sure of (scores near 0.5), or those several models disagree on. For rare positives, first narrow the pool to the near neighbours of known positives | A labelling budget and a working model |
| Pseudo-labels | Train a high-precision model, add its most confident predictions as labels, retrain, and repeat | Many unlabelled rows and a model that is precise at the top |
| Near neighbours | When a person confirms a label, find similar items (by embedding or edit distance) and send them for review | Growing a slice where errors cluster |

Weak supervision can stand in for many hand labels: at Google, 10 labelling functions matched a classifier trained on 80,000 hand-labelled items (Yan, *Bootstrapping Labels*). Pseudo-labels and weak labels are for training; they are never the evaluation set.

## Labels the product already has

Look for labels the product already collects: the names users give their lists or shelves, or a search ranked without a model whose clicks and purchases later train one. Shipping the rule first works the same way: it collects the labels the model will need.

## Labels that change after they are recorded

A purchase counts as a conversion until the return window closes; a payment looks legitimate until it is charged back. A model trained on labels that have not settled learns from wrong ones, and once its decisions shape the next training set, its errors compound. Train only on rows whose label has settled, and measure how long that takes: the share of labels that flip after a day, a week and a month.

## Negatives for rankers and retrieval

Which examples count as negatives is a choice that changes the model. Items shown and not clicked, random items, and a mix of both give different models: in one search system, shown-but-not-clicked negatives gave 55% less recall than random ones, while another team did better with them once its loss accounted for them (Yan, *The Metagame of Applying ML*). Try the options on validation and write down the choice.

Hard negatives (items the model gets wrong or is unsure of, and their look-alikes) help in a mix: hard negatives alone did no better than random ones in one retrieval system, because most real candidates are easy (Yan, *More Design Patterns for ML Systems*).

## A set checked by hand, for evaluation

Weak labels, pseudo-labels and a rule's outputs are fine for training. Evaluate on labels people checked: scored on labels a rule wrote, the rule looks perfect, and a model looks good for copying it. Label the evaluation set with the same guideline, measure its agreement, keep it fresh, and record it in the Data section of `MODEL.md`.
