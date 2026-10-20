# Worked framings

Five product models framed the way the Decision section of `MODEL.md` asks. The numbers are illustrations, not benchmarks.

## Contents

- Content moderation
- Claims investigation
- Lead scoring
- Delivery estimates
- Search ranking
- Other framings of the same decision
- Rules that are hard to beat
- Questions for the threshold owner

## Content moderation

| | |
|---|---|
| Action | Hide a post until a moderator reviews it |
| Moment | At upload; only the post, its author's history and the context are known |
| Unit | Harmful posts seen by users, and harmless posts held back |
| False positive | A harmless post hidden: a frustrated author, a moderator's minute |
| False negative | A harmful post left up: harm to users, complaints, possible legal exposure |
| Owner | The trust and safety lead, who also owns moderator capacity |
| Rule to beat | The current term list and user reports, scored on the same weeks of posts |
| Ladder | User trust and retention → harmful views per thousand → share of reports upheld → recall at the review capacity on later posts |

If a term list catches most of what a model would, the list ships first, and moderators' decisions on what it misses become the labels a model will need.

## Claims investigation

| | |
|---|---|
| Action | Send an insurance claim to an investigator before paying it |
| Moment | At submission; the claim, the policy and the claimant's history are known, the investigation's result is not |
| Unit | Euros: investigations times their cost, plus the amount of every fraudulent claim paid |
| False positive | An investigation of an honest claim: the fee, a delayed payment, an annoyed customer |
| False negative | The full amount of a fraudulent claim |
| Owner | The claims manager, who also owns investigator capacity |
| Rule to beat | Today's rule (amount above a limit, policy younger than a month), scored in euros on the same claims |
| Ladder | Loss ratio → fraud euros stopped per investigation → share of investigations that find fraud → expected cost on held-out claims |

Because a miss costs the claim's amount, the cheapest policy depends on the amount: investigate when the probability of fraud times the amount exceeds the cost of an investigation. That needs calibrated scores. Check investigator capacity before proposing a policy that multiplies the queue.

## Lead scoring

| | |
|---|---|
| Action | Put a lead on the sales team's demo list for the week |
| Moment | Monday morning, with data up to Sunday night |
| Unit | Deals won from demos, with a capacity of about 40 demos a week |
| False positive | A demo with a lead that was never going to buy: a salesperson's hour |
| False negative | A buyer who never got a demo; costly only if a demo would have won them |
| Owner | The head of sales |
| Rule to beat | The current rule (company size and pages visited); 40 random leads as the floor |
| Ladder | Revenue → deals won per week → demo-to-deal rate against a held-out group not offered demos → won deals among the top 40 on later weeks |

The model ranks; capacity sets the cut. Predicting who will buy is not predicting who a demo will convince: keep a flagged group without demos, or the program cannot be judged.

## Delivery estimates

| | |
|---|---|
| Action | Show "arrives in 25 to 35 minutes" at checkout |
| Moment | When the customer reaches checkout; anything after that (the courier assigned, the actual prep time) is unknown |
| Unit | Orders arriving inside the promised window; orders lost to long estimates |
| Errors | Late costs more than early: a late order is a support ticket and maybe a lost customer, an early one a pleasant surprise. Padding every estimate loses orders |
| Owner | The product manager for checkout, with operations |
| Rule to beat | The restaurant's average prep time plus distance over average courier speed, scored on last quarter's orders |
| Ladder | Repeat orders → on-time rate within the promise → "where is my order" tickets and checkout conversion → pinball loss at the promised quantile |

The asymmetry points to a quantile loss, not squared error. Promising the median is late half the time; the quantile to promise is a product decision, best settled by an experiment.

## Search ranking

| | |
|---|---|
| Action | Order the results for a marketplace search |
| Moment | When the query arrives; the query, the shopper's history and each listing's features are known |
| Unit | Purchases per search, and searches that end in nothing |
| Errors | A weak listing on top wastes the most-seen slot; a strong listing buried is never seen, and never collects the clicks it would need to rise |
| Owner | The product manager for search |
| Rule to beat | Today's order, such as best-selling first |
| Ladder | Marketplace revenue and repeat buyers → purchases per search → clicks on the first results → a ranking metric on held-out searches, corrected for position |

Clicks and purchases on a ranked list measure position as much as appeal, because the current order decides what could be clicked. Framing a ranker includes finding out whether any traffic is shown in random order: that traffic is the only unbiased evidence.

## Other framings of the same decision

The first framing proposed is rarely the only one, and the choice can matter more than the model. Name at least one alternative and say why it lost.

| Decision | Framings |
|---|---|
| Stop fraud | Flag the fraudulent payments; clear the safe ones and send the rest to review; estimate the amount at risk rather than a yes or no |
| Recommend videos | Predict the rating, the chance a video is played, or the minutes watched. Each is a different stand-in for "a good recommendation", and the choice moves the online test's result |
| Moderate posts | Remove the harmful ones; or order the review queue so moderators see the likeliest harm first, within their capacity |

## Rules that are hard to beat

Simple rules are often hard to beat, for a fraction of the work. Score the one that fits before training anything.

| Problem | Rule to try first |
|---|---|
| Recommendations | Last period's most popular items, overall or per category; items often bought or viewed together |
| Classifying items by their text | Keyword or regular-expression rules on the title: a title with "ring" or "wedding band" files under rings |
| Review or comment spam | Many posts from one address, posts at odd hours, near-copies of other posts from the same day |
| Outliers | Values outside the interquartile range, per segment |
| Forecasts | A moving average of recent periods, or the last value |
| Matching names or addresses | A dictionary of known variants |

The same rules, written as labelling functions that return a label or abstain, can produce the first labels when none exist (`building-datasets`, reference/labels.md).

Move from the rule to a model when the rule works reasonably well but keeping it right costs more than a model would. The sign is a rule set nobody can change without breaking another rule. Labels you can trust come first: labels written by people who gain from a wrong answer (sellers filing products under the category with the lowest fee) teach the model their gaming, so check a sample by hand.

## Questions for the threshold owner

1. What does the product do differently when the prediction says yes? What happens today instead?
2. What does each kind of mistake cost you, roughly, in money, time or customers? Which one is worse, and by how much?
3. How many positives can you act on per day, week or month?
4. How do you decide today, and how well does that work? Is anyone keeping score?
5. When do we learn whether a prediction was right, and from what record?
6. What would make you turn the model off?
7. If two goals pull apart (conversion and revenue, this session and the next year), which one decides, and over what period is it measured?
