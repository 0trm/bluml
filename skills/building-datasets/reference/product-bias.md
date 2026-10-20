# What the product puts in the labels

A product model learns from data its own product generated. What the product showed, ranked first, reviewed or acted on decides which rows have labels and what those labels mean.

## Contents

- Position and exposure in rankings
- Selection: labels only where the product acted
- Interventions change what the label means
- Random traffic: the only unbiased evidence
- Corrections
- Counterfactual estimates

## Position and exposure in rankings

People click what is on top. A click on slot 1 says the item was seen; no click on slot 10 often says nothing. A model trained on raw clicks learns where the current ranker put things, then puts them there again, and an offline comparison on the same logs rewards whoever made the logs (Rules of ML #35, #36).

A popularity rule makes this a loop: items that were on top get clicks, so they stay on top; new items start at the bottom, collect few clicks, and stay there. Signs of the loop: fresh items rarely reach the top slots; the logged click rate falls steeply by position; most clicks go to a few items.

## Selection: labels only where the product acted

- A fraud model learns from payments that were reviewed or charged back; payments the old rule blocked have no outcome.
- A credit model sees repayment only for approved loans.
- A spam filter sees user verdicts only for mail it let through (Rules of ML #34).
- A delivery model sees delivery times only for orders that were not cancelled.
- A demand forecast sees sales, and sales stop at the stock the last forecast ordered. A forecast that runs low empties shelves, the lost sales are never recorded, and the next model learns lower demand while its error still looks fine.

The model then learns the world as the old system let it be seen. Count the rows with no outcome, and ask whether they differ from the rest.

## Interventions change what the label means

Once the model drives action, its labels record the action too. Accounts that were called and stayed may have been saved by the call; a recommendation that was clicked may have been clicked because it was shown. A model retrained on those labels learns to stop flagging the accounts its calls saved. Keep a group that is flagged but not acted on, so the effect of the action and the accuracy of the model can both be measured.

## Random traffic: the only unbiased evidence

Look for it before modelling:

- a share of visits shown in random order, or with one random item inserted;
- a holdout that is never filtered or never treated (Rules of ML #34 suggests about 1% of traffic for a filter);
- a control group left out of a campaign.

On random traffic, position is unrelated to the item, so it measures the position effect and gives an unbiased test of any ranking. If none exists, the offline comparison favours the current system: say so, and propose keeping a small random slice from now on.

The slice can be small. In practice it is a random bucket of users, 1% of traffic served by a random policy, or a few random items (5%) mixed into every list before re-ranking. A bandit (Thompson sampling, upper confidence bounds) aims exploration at the items it is least sure of, so it loses less to poor items than uniform chance does; it is a different design, beyond this file.

## Corrections

| Method | How | Needs |
|---|---|---|
| Position as a feature | Train with the position (or the slot) as a feature; at scoring time give every candidate the same position, since the order is not decided yet (Rules of ML #36). Keep position out of crosses with other features | Logged positions |
| Inverse propensity weighting | Estimate the chance each slot is seen (from random traffic: click rate by position); weight each clicked example by one over it | Random traffic or a click model |
| Train or evaluate on random traffic | Use only the random slice to compare rankings, or to fit the position effect | Enough random traffic: thousands of visits for a ranking comparison |
| Counterfactual estimate | Estimate a new policy's clicks from logged data, weighting by how likely the logging policy was to show what the new one would (below) | Logged propensities |
| Online test | A/B test or interleaving: the only direct measure for a ranker | Traffic and time |

Offline corrections reduce the bias; they do not remove the need for an online test before a ranker replaces the current one.

## Counterfactual estimates

Inverse propensity scoring (IPS) estimates from logs what an online test would show. Each logged reward (a click, a purchase) is weighted by how much more or less often the new policy would take the logged action than the logging policy did:

```text
weight = P(new policy takes the logged action) ÷ P(logging policy took it)
IPS    = mean over logged rows of (weight × reward)
SNIPS  = sum(weight × reward) ÷ sum(weight)
```

If the current system shows an item in a slot with probability 0.4 and the new policy would with 0.6, each click logged there counts 1.5 times.

- **Logged propensities:** the probability that the logging policy took each action. Impression counts are the most direct source. Normalized scores are propensities only when the policy samples from them; a policy that always shows its top items has none to log.
- **Support:** an action the logging policy never took has no logged rows, so the estimate cannot see what the new policy gains or loses by taking it. Give every eligible item a nonzero chance of being shown, or keep a random slice.
- **Variance:** a click logged at 0.001 and replayed at 0.1 counts 100 times, so a few rows decide the estimate. Keep candidates close to the current policy, cap the weights, or self-normalize (SNIPS), which had the lowest error without tuning in the experiments Yan reports (Yan, *Counterfactual Evaluation for Recommendation Systems*).

Use it to decide which candidates earn an online test, and turn to it when offline metrics stop agreeing with online results. It does not replace the test.
