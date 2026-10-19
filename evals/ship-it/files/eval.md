# recs_v2 offline evaluation

- Data: home feed impressions from 2026-07-01 to 2026-09-30 (warehouse export), 4.1M rows; a 5,000-row sample is in `data/impressions_sample.csv`
- Split: 80/20 random, seed 7
- recs_v1 (current, logistic regression): AUC 0.721
- recs_v2 (HistGradientBoosting, 300 iterations): AUC 0.742
- Conclusion: v2 is 2.1 AUC points better. Ready to launch.
