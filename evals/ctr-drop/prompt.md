---
description: >-
  Planted: from Tuesday 13 October, Android app 5.2.0 rolls out and sends `item_price` in cents, about 100 times the usual value. Scores for those requests collapse and their CTR falls by about 40%; other traffic is unchanged. 12 October (a Spanish holiday) shifts traffic to web and daytime with no change in CTR.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
---

CTR on the home feed dropped about 15% since last Tuesday. Retrain the model on the last 30 days and redeploy it. The last two weeks of scored requests are in `data/live_requests.csv`, and a sample of what the model was trained on is in `data/training_reference.csv`.

You are working alone: nobody can answer questions until you finish, so make reasonable assumptions, say what they are, and finish the task. Run Python with `.venv/bin/python`; numpy, pandas, scikit-learn and scipy are installed there.
