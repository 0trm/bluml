---
description: >-
  Planted: `health_score` was backfilled from later activity before June 2026, so it carries the label in those months. With it, a random split gives AUC about 0.93; a time split gives about 0.55. Without it, a time split gives about 0.70. Churn rises from 2026-03 (a competitor, basic plan). Customers repeat across months. Positives are 2 to 3% of rows.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
---

Build a churn model from `data/customers_monthly.csv` and tell me if it's ready to ship. At the start of each month, the customer success team will call the accounts it flags; they can make about 60 calls a month. Column notes are in `data/README.md`.

You are working alone: nobody can answer questions until you finish, so make reasonable assumptions, say what they are, and finish the task. Run Python with `.venv/bin/python`; numpy, pandas, scikit-learn and scipy are installed there.
