# Error analysis

Reading errors tells you what to fix next. Counting them tells you whether it is worth fixing.

## The procedure

1. Score validation rows and take a random sample of errors: 50 to 100, split between false positives and false negatives in proportion to what they cost.
2. Read each error with its features and raw inputs. Write a short tag for why it is wrong. Tags emerge as you read; merge them at the end.
3. Count tags. For each, estimate the gap to the best achievable on that group: the rule's error there, human agreement, or the share of labels that are noise.
4. Prioritize by share of errors × gap × how cheap the fix is.
5. Decide data or model for the top tag, fix it, and re-run the evaluation on the same validation rows.

## A worked tagging table

A moderation classifier for abusive posts, 80 errors read from validation:

| Tag | Errors | Share | Best achievable | Fix |
|---|---|---|---|---|
| Moderators disagree with each other on the label | 28 | 35% | Not fixable by a model: about 4% of labels flip on a second review | Audit labels with two reviewers; report the ceiling |
| Quoted or reported abuse ("someone called me ...") | 21 | 26% | Moderators get these right | More labelled examples; a feature for quotation |
| Posts not in English | 17 | 21% | The term list misses them too | Collect labels in the top languages |
| Abuse inside an image | 14 | 18% | Moderators get these right | A text-from-image feature, or route images to people |

The largest group is label disagreement, which no model fixes; the next two are data problems. Without the table, the natural move would have been a bigger model.

## Data or model

| Signs it is data | Signs it is the model |
|---|---|
| Errors cluster in a slice with few training rows | Errors spread evenly; training error is high too |
| Labels in the error sample are wrong or inconsistent | A simpler model makes the same errors as a richer one only on hard cases |
| The information needed is not in any feature | The information is in the features but the model cannot combine it (interactions, sequence) |

Rules of ML #26: look for patterns in the errors and turn them into features. #41: on a plateau, add a new source of information rather than refining the existing ones.

## Writing it down

Put the tag table, or its top three rows, under "Errors left" in the Evaluation section of `MODEL.md`, with the fix chosen for each.
