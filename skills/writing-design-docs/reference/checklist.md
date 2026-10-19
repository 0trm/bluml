# Reviewer checklist

The questions a senior reviewer asks of each section. Run them on your own draft first; every "no" is a gap to fill or a risk to name. The structure follows Eugene Yan, [How to Write Design Docs for Machine Learning Systems](https://eugeneyan.com/writing/ml-design-docs/) (2021); the questions are saffml's.

## Contents

- Why and success
- Requirements and constraints
- Methodology
- Implementation
- Risks and alternatives
- The review itself

## Why and success

- Can a reader say, after the overview, what will be different for users?
- Is it clear why improving the current system is not enough?
- Is the metric that decides the online test a product metric, with the smallest change worth shipping stated?
- Are there guardrails for what the model could make worse while improving its metric?

## Requirements and constraints

- Is every requirement testable: a number, a share, a percentile?
- Are throughput, latency, freshness and cost given as numbers, with the assumptions (traffic, catalogue, users) behind them?
- Is personal data in the inputs named, with how it is stored, retained and deleted?
- Is out of scope written down, with the debt it creates and when it is paid?

## Methodology

- Is the framing justified against at least one other framing?
- If the model predicts a surrogate (clicks for satisfaction, a score for a decision), is the gap between the two acknowledged and measured?
- Does every feature exist at prediction time, and are labels' delays stated?
- Is the rule measured on the same data, and is it the first baseline?
- Does the split mirror serving?
- Is the online test designed: unit, success and guardrail metrics, duration, decision rule?
- Does the product's own behaviour shape the labels (position, what was shown, an intervention), and how is that corrected?
- Where do people stay in the loop, and do their corrections become labels?

## Implementation

- Is there a diagram, and does every arrow have an owner?
- What happens when the model, a feature source or the service fails?
- Is serving batch unless something requires online?
- Are monitors defined for inputs, outputs and outcomes, with someone paged?
- Is the rollback a configuration change, rehearsed before launch?
- Does the cost compare with the value expected?

## Risks and alternatives

- Are the risks specific, each with a mitigation or a way to watch it?
- Are the alternatives real (including keeping the rule), each with a reason for rejection?

## The review itself

- Does the doc say what the review must decide?
- Did a pre-review happen, so the formal review finds no major redesign?
- Are decisions from the review recorded in the doc and in `MODEL.md`?
