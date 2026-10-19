---
name: writing-design-docs
description: Writes the design doc for a product ML system after framing and before building, so reviewers can catch design flaws while changes are cheap. Covers why now and how success is measured, quantified requirements and constraints, scope and assumptions, the methodology (problem framing, data, techniques, validation, the online test, human review), the implementation (serving, scale, latency, privacy, security, monitoring, cost, integration, rollback), risks, alternatives rejected and what reviewers must decide; runs a rough pre-review, then a formal review. Use when asked for a design doc, technical spec, RFC, proposal or plan for an ML model or system, when a framed model is ambiguous, high impact or more than a few days of work, or before building the data pipeline and serving for a new model.
---

# Writing design docs

A design doc is where an ML system is cheapest to change. Writing it forces the thinking; reviewing it finds the flaw that would otherwise surface in week six, or after launch. It is written for reviewers who will challenge it, not to record what was already decided.

Read `MODEL.md` first. The design doc starts from its Decision section (what the product does with each prediction, what each error costs, the rule to beat): link to it, don't restate it. If the Decision gate is not ticked, run `framing-models` first.

## 1. Decide how much doc the work needs

- **A full doc** when the problem is ambiguous, the impact is high, or the build takes more than a few days: a new model, a new serving path, a change other teams depend on.
- **A design section in `MODEL.md`** (a page of the same headings, in bullets) for a small model or a change to an existing one.
- **No doc** for a retrain, a feature fix or a threshold change; record those in the `MODEL.md` log.

## 2. Answer the feasibility questions first

Before writing the methodology, spend a short, fixed time on the questions that decide it: does the data exist at prediction time, how many labels are there and how late do they arrive, what does the rule score, does a simple baseline beat it at all. Put the numbers in the doc. A design built on unmeasured assumptions gets redesigned in review.

## 3. Draft for pre-review

Copy [templates/DESIGN.md](templates/DESIGN.md) beside `MODEL.md` (or into the team's document tool) and fill it as an outline: bullets, open questions, rough numbers. Mark it "pre-review draft" at the top. It goes to one to three people (a teammate, a senior engineer, the threshold owner) to narrow the options early. Expect most of it to change. Collect their questions; the ones a reader will also ask go into the FAQ.

## 4. Write the review version

The review version is prose, with numbers, for senior engineers and the people who decide. It must have:

- **Why, and why now,** with what improving the current system instead would get, and why that is not enough.
- **Success criteria** from the metric ladder: the product metric the online test decides on, the smallest change worth shipping (the break-even gain from the case in `MODEL.md`), the guardrails, and operational capabilities (a rollback, a fallback, a latency budget).
- **Requirements and constraints, quantified.** Functional ones from the user's side (share of users with a result, a cap on false positives, low-confidence cases sent to a person); non-functional ones as numbers (requests per second, p99 latency, cost per month, freshness, privacy rules). Scope in and out, and the assumptions behind the numbers (catalogue size, users, traffic).
- **Methodology:** the problem as framed (and the surrogate problem, if the model predicts something other than the goal), the data for training and for serving with its labels and their delay, the techniques starting from the baselines, the validation (a split that mirrors serving, offline metrics as proxies, the online test with its unit, success and guardrail metrics and decision rule), and where people stay in the loop (overrides, exclusion lists, review above a value).
- **Implementation:** a system-context or data-flow diagram, batch or online serving with the fallback, scale and latency, security, data privacy (which personal data is used, stored and deleted, and how), monitoring and alerts, cost (build, upkeep, training and serving compute, and what the added latency costs the product metric, against the value, from the case in `MODEL.md`), integration points (the API, upstream data, downstream users), rollout and rollback.
- **Risks and uncertainties:** what could make this fail, including what the product puts into its own labels (a ranking, a recommendation or an intervention that changes the outcome it predicts).
- **Alternatives considered:** each with its pros and cons and why it was rejected, including "keep the rule" and "improve the current system".
- **What the review must decide:** the decisions needed, the risks to check, the help wanted. Reviewers who know what is asked of them give useful feedback.

Offline results, benchmarks, milestones, a glossary and the pre-review FAQ go in the appendix. [reference/checklist.md](reference/checklist.md) lists the questions reviewers ask of each section; run it on your draft before anyone else does.

## 5. Run the review, then record it

The author proposes; reviewers and the threshold owner decide. Send the doc ahead with the asks, take decisions and objections in the doc's comments or the meeting, and change the design where they land. Then set the status to approved with the date and reviewers, and fill the Design section of `MODEL.md`: the link, reviewers, decisions taken, and risks left open. A major change found in formal review means the pre-review was skipped or too shallow; say so in the log.

## 6. Keep it true

When the build departs from the design (a different model, a new data source, online instead of batch), update the doc and add a dated line to its change log and to `MODEL.md`. A design doc that describes a system nobody built misleads the next engineer.

## Stop signs

- A doc that restates the template's headings without numbers.
- No alternatives, or alternatives that were never real options.
- No measured baseline: the rule's number is missing or assumed.
- Requirements nobody can test ("fast", "accurate", "scalable").
- Personal data in the inputs with no privacy section.
- A formal review that is the first time anyone has seen the design.
