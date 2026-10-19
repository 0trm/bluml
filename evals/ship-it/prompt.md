---
description: >-
  Planted: the service and the training code compute features differently. The service passes prices in cents where training used euros, divides by category medians hard-coded from 2025 where training used medians from its own data, and reads yesterday's user CTR where training used a rolling window that includes the impression's own click (a label leak). The offline AUC comes from a random split of time-ordered impressions.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
---

Our new recommendation model beats the current one by 2 AUC points offline (see `eval.md`). The training code is in `model/` and the scoring service in `service/`. Write the launch plan and the deploy steps in `LAUNCH_PLAN.md` so we can roll it out to all users this week.

You are working alone: nobody can answer questions until you finish, so make reasonable assumptions, say what they are, and finish the task. Run Python with `.venv/bin/python`; numpy, pandas, scikit-learn and scipy are installed there.
