---
name: framing-models
description: Starts any product ML task. Frames the prediction problem before data or training work and decides whether a model should be built at all: what the product does with each prediction, when it predicts, what each kind of error costs and who owns the threshold, the rule or current system a model must beat, measured, and the business case: whether the gain over the rule pays for building and running the model, compute and latency included, with its break-even gain and payback. Creates the model's MODEL.md, which the other bluML skills read and update. Use first whenever asked to build, train or ship a model (classifier, ranker, recommender, scoring, churn, fraud, forecast or "some ML"), whenever a request names a model before the decision it serves, and when asked whether a model is worth it, its ROI or what it costs to run.
---

# Framing models

A model earns its place only when it improves a decision the product already makes, by more than a rule would, at a cost someone has agreed to pay. Settle that before touching data, and write the answer down.

## Start from the record

Look for the model's `MODEL.md`: beside its code, or under `models/<name>/`. If it exists, read it and continue with the skill for its stage (design: `writing-design-docs`, data: `building-datasets`, training: `training-models`, evaluation: `evaluating-models`, launch: `launching-models`, live: `monitoring-models`). If it doesn't, copy [templates/MODEL.md](templates/MODEL.md) next to the model's code and fill its Decision section as you work through the steps below.

## 1. Name the decision

Write down, in the product's words:

- **The action:** what the product does when the prediction says yes, or how it uses the score (hide the post, investigate the claim, book the demo, order the search results), and who or what takes the action.
- **The moment:** when the prediction is made, and what is known at that moment. This fixes which data the model may use, so be exact: "at checkout", "at 06:00 on the first of the month", "when the page is requested".
- **The unit:** what the decision is judged in. Euros, minutes late, demos booked, posts wrongly removed, purchases per search.
- **Whether acting changes the outcome:** when the action is meant to change what the model predicts (a call to keep a customer, a discount to convert a lead), the model predicts risk, not the effect of acting. Plan a group that is flagged but left alone, so the action itself can be judged.

When the request names a solution, ask why until the problem shows. "Rank fast-shipping products higher": why? They arrive sooner. Why does that matter? Late orders bring complaints. The problem is late orders, and what it needs may be a better delivery estimate, not a ranker. Frame the problem, and note the other framings it allows: a fraud model can flag the fraudulent payments or clear the safe ones.

If nobody can say what the product does with the prediction, stop and ask. A model that serves no decision cannot be judged.

## 2. Price the errors

A model is wrong in two directions, and they rarely cost the same.

- **Classifiers:** what a false positive costs and what a false negative costs, each in the decision's unit. A harmful post left up costs harm and a complaint; a harmless post sent to review costs a moderator a minute. A fraudulent claim paid costs its amount; an investigation costs a fixed fee.
- **Rankers:** what a poor item at the top costs, compared with a good item buried.
- **Forecasts:** whether over- and under-prediction cost the same. A late delivery estimate costs more than an early one, which points at a quantile, not the mean.
- **Capacity:** a sales team that can run 40 demos a week needs the best 40 leads, not a probability threshold. Write the limit down.
- **The threshold owner:** the person who answers for the cost of each error, such as the trust and safety lead, the claims manager or the head of sales. The model proposes an operating point; the owner sets it.

When the costs are unknown, assume a ratio, set the operating point from it, show how the answer moves if the ratio is off by a factor of two, and list each assumption as a question for the owner. Do not leave the costs out because nobody gave them, and do not let a default threshold of 0.5 stand in for a cost ratio nobody chose.

## 3. Measure the rule to beat

Every product already decides somehow: by hand, with a rule, with a formula, or with an older model. That is the baseline, and its number is the bar.

1. If a rule or system exists, score it on recent data, in the decision's unit.
2. If people decide by hand, write the simplest rule a person would use (a cutoff on one field, a lookup table, most popular first) and score that. [reference/framings.md](reference/framings.md) lists rules that are hard to beat for common problems.
3. Add the trivial baselines at the same operating point: the majority class, and random choice at the same capacity.
4. Score every baseline on the same rows, held out by time, that the model will later be scored on.

A rule that ships today is also the fallback when the model fails, and the logging that collects the labels the model will need. Written as labelling functions, the same rules can produce the first labels (`building-datasets`, reference/labels.md).

When the current system decides what is shown or acted on (the order of a list, which payments are reviewed, which accounts are called), it also wrote the labels. What it never showed or acted on has no outcome, and what it favours collects more evidence each day, so it stays favoured. A model trained on those logs inherits the loop, and scoring on the same logs flatters the system that made them. Name the loop under "What the product put in the labels" in `MODEL.md`, keep or start a slice of random traffic, and read `building-datasets` step 6 before training.

## 4. Write the metric ladder

Connect the number training will move to the number the business cares about:

`business metric → product metric → online proxy → offline metric`

For example: retention → share of orders arriving within the promised window → "where is my order" tickets → pinball loss at the 80th percentile on held-out orders. Training moves the bottom rung. If moving it cannot move the top, the objective is wrong; fix it here, not after launch.

When stakeholders want different top rungs (conversion or revenue; this session or the customer's next year), do not optimize a blend nobody chose. The owner picks the rung the model is judged on and the period it is measured over; the others become guardrails. Write both down.

## 5. Make the case

A gain over the rule is worth building only if it pays for the model, every month. Put numbers on both sides, in money:

- **Value:** decisions per month × the gain over the rule per decision × what one unit of the decision is worth. Count only the decisions the model would change: a model for one category or one market moves only its share. The gain is an assumption until evaluation: give a range. For a classifier, the ceiling is the rule's error cost per month; a perfect model saves no more.
- **Build, once:** engineer weeks at the team's loaded cost, labels, the data pipeline, the launch. A timebox is a stretch goal, not an estimate: multiply it by 1.5 to 3.
- **Run, every month:** upkeep (a share of an engineer for on-call, monitors and retrain reviews), pipelines and feature storage, and training compute (cost per run, searches included, times runs per month).
- **Per decision:** serving compute (online serving is sized for peak traffic), paid calls, and human work each prediction triggers that the error costs do not already count.
- **Latency:** a model inside a user-facing request slows every request, and slower pages lose users, including on requests the model gets right. Price it as the product metric lost per 100 ms (from a slowdown test, or an assumption marked as one) times the delay the model adds. Batch serving adds none.

Then write three numbers: net value per month, the **break-even gain** (monthly cost ÷ (decisions per month × value of one unit): the smallest gain over the rule that pays), and **payback** (build cost ÷ net value per month). Show how they move when the gain halves, and name the input that flips the answer. When the ceiling is below the monthly cost, no model can pay: the rule ships, and nothing needs building.

Take prices from the team's own bill and history; when a number is unknown, assume it, mark it, and list it as a question for its owner. [reference/business-case.md](reference/business-case.md) lists the costs teams forget, how to measure latency and compute, a worked case, and how the case is updated at each stage.

## 6. Decide

Build a model when all of these hold:

- The rule would need too many cases, or cases too fuzzy, to write by hand, or it already has so many that changing one breaks another.
- The patterns shift, so a hand-written rule goes stale.
- Mistakes are tolerable or caught downstream.
- Labels exist and a small set labelled by hand agrees with them, or the product can start collecting them.
- The expected gain clears the break-even gain, and the build pays back well before the product stops making this decision this way.

Then write one of three outcomes:

- **The rule ships.** The rule is good enough, or the expected gain sits below the break-even gain or only clears it at the top of its range. Write the rule's expected performance and the case, and stop. Revisit when labels accumulate, costs fall, or the rule needs exceptions.
- **Build a model.** Name the break-even gain it must clear over the rule, in the decision's unit. Consider keeping the rule in front, settling the cases it is sure of, with the model deciding only the rest: a cascade costs less to run (`launching-models`, reference/serving.md). Unless the model is small, the next step is a design doc reviewed before building (`writing-design-docs`).
- **Not now.** There is no label and no way to collect one, or the data holds no signal. Check every source of labels before settling on it: user reports, an existing system, annotators, a rule that is right when it fires (`building-datasets`, reference/labels.md). Say what would change the answer.

## Write it down

Fill the Decision section of `MODEL.md`, tick the gate items that hold, and add a dated line to the log. Leave unticked items unticked and say why.

## Report

Lead with the outcome in one line: the rule ships, build a model, or not now, and why. Then give the decision, the costs and their owner, the rule's number, the case (net value per month, break-even gain, payback), and the open questions for the owner. Keep assumptions visible: list each one next to the number it affects.

## Stop signs

- A request for "a model" with no decision behind it.
- A label nobody can observe, or one that arrives after the decision stops mattering.
- A rule that already meets the need.
- A request to "just train something" on a table before anyone has said what the prediction will change.
- A model on a busy user-facing path, with nobody able to say what its latency costs.
- A use of the prediction that works against the people it scores: an insurer asking which customers will stay healthy, so it can sell to them and avoid the rest.

For worked framings of common product models (content moderation, claims investigation, lead scoring, delivery estimates, search ranking), other framings of the same decision, rules that are hard to beat, and the questions to ask the threshold owner, read [reference/framings.md](reference/framings.md).
