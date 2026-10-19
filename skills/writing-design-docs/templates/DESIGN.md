# {model or system}: design doc

| Status | Author | Reviewers | Decision record |
|---|---|---|---|
| {pre-review draft, in review, approved YYYY-MM-DD} | {who} | {names and roles} | [MODEL.md](MODEL.md) |

**What this review must decide:** {the decisions needed, the risks to check, the help wanted}

## 1. Overview

{Three to five sentences: the problem, the proposed solution, and the outcome expected.}

## 2. Why, and why now

{The motivation and the customer or business benefit. What improving the current system would get instead, and why that is not enough. The decision the model serves and what each error costs are in MODEL.md: link, don't restate.}

## 3. Success criteria

- **Decides the online test:** {the product metric, and the smallest change worth shipping: the break-even gain from the case in MODEL.md}
- **Guardrails:** {metrics that must not get worse, with their margins}
- **Operational:** {rollback without a deploy, a fallback, a latency budget, freshness}

## 4. Requirements and constraints

- **Functional, from the user's side:** {e.g. at least five results for 95% of users; at most 1 false alarm in 200; predictions below a confidence go to a person}
- **Non-functional:** {requests per second, p99 latency, freshness, cost per month, availability}
- **Data and privacy:** {personal data used, where it is stored, how long, who can see it, the rules that apply}
- **In scope / out of scope:** {what this version does and deliberately does not}
- **Assumptions:** {catalogue size, users, traffic, label volume, growth}

## 5. Methodology

### 5.1 Problem statement

{How the problem is framed (classification, ranking, a quantile forecast; candidate generation then ranking), and the surrogate problem if the model predicts something other than the goal.}

### 5.2 Data

{Training data and the entities in it; the label, its window and its delay; the inputs available at serving time; what the current product put in the labels.}

### 5.3 Techniques

{The baselines (the rule, a simple model), the candidates, the features and how they are prepared.}

### 5.4 Validation and experimentation

{The split and why it mirrors serving; the offline metric at the operating point and why it is a fair proxy; the online test: randomization unit, success and guardrail metrics, duration, decision rule.}

### 5.5 Humans in the loop

{Overrides, exclusion lists, review above a value or below a confidence, how people's corrections become labels.}

## 6. Implementation

### 6.1 High-level design

{A system-context or data-flow diagram, and a paragraph walking through it.}

### 6.2 Serving, scale and performance

{Batch or online, the fallback, throughput and latency targets and how they are met (precomputation, caching), scaling.}

### 6.3 Security and data privacy

{Authentication of callers; how personal data is protected, retained and deleted.}

### 6.4 Monitoring and alerts

{Inputs, outputs and outcomes watched, alert thresholds, who is paged.}

### 6.5 Cost

{From the case in MODEL.md, updated for this design: build cost; every month, upkeep, pipelines, training compute and serving compute (online is sized for peak); the latency the model adds and what it costs the product metric; against the value expected. The break-even gain, payback, and the input that flips the answer.}

### 6.6 Integration points

{The API (inputs, outputs, errors), upstream data owners, downstream consumers.}

### 6.7 Rollout and rollback

{Shadow, canary, online test, everyone; how to switch back and what triggers it.}

## 7. Risks and uncertainties

{Known unknowns and how each is mitigated or watched; what is still unknown and how it will be found out.}

## 8. Alternatives considered

| Alternative | For | Against | Why rejected |
|---|---|---|---|
| Keep the rule | | | |
| {alternative} | | | |

## Appendix

- **Offline results:** {tables, with the baseline beside each number}
- **Benchmarks:** {throughput and latency against instance size}
- **Milestones:** {dates and what each delivers}
- **FAQ from pre-review:** {questions and answers}
- **Glossary and references**

## Change log

- {YYYY-MM-DD}: {what changed in the design, and why}
