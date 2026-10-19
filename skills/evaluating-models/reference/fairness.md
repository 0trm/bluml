# Fairness checks

When a model's decisions fall on people (credit, hiring, pricing, moderation, fraud review), check whether its errors and decisions fall evenly across the groups the product is responsible to. The Machine Learning Crash Course's fairness module is the source for the definitions below.

## Which check

| Check | Holds when | Use when |
|---|---|---|
| Demographic parity | The share of people acted on is the same across groups | Access to an opportunity should not depend on the group, whatever the label says |
| Equality of opportunity | Among people who are truly positive, the share acted on is the same across groups (equal recall) | Benefits go to the qualified, and missing a qualified person from one group is the harm |
| Equalized odds | Equal recall and equal false positive rate across groups | Both kinds of error harm people |
| Counterfactual fairness | Changing only the sensitive attribute does not change the decision | Checking a single decision for dependence on the attribute |

The definitions conflict when base rates differ across groups: a model cannot in general satisfy all of them at once. Choose the one that matches the harm, with the threshold owner, and write the choice in `MODEL.md`.

## How to run it

1. Name the groups and where the attribute comes from. If it is not recorded, say so; proxies (postcode, language) can still carry it.
2. Use `slices.py` with `--by <group>` and the metric the chosen check needs: `flag_rate` for parity, `recall` for opportunity, both recall and the false positive rate for equalized odds.
3. Read the intervals; small groups give wide ones.
4. Look at the training data for the cause: groups underrepresented, labels produced by a biased process (reporting bias, historical decisions), features that stand in for the attribute.
5. Mitigate at the source when possible (more data, better labels), then by policy (group-aware thresholds where allowed), and record the trade-off in accuracy.

## Bias in the data itself

Reporting bias, historical bias, sampling bias and group attribution bias enter through how labels and rows were produced, often by the product's own past decisions. `building-datasets` (reference/product-bias.md) covers the product-made ones.
