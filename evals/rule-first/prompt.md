---
description: >-
  Planted: a keyword rule (invoice, refund, payment, card, receipt...) routes about 97% of tickets correctly; a text model gains about two points. About 1.5% of labels are wrong because agents sometimes leave a ticket in the wrong queue.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
---

Our support lead wants a model that routes each incoming ticket to the billing queue or the general queue. Today agents triage every ticket by hand. `data/tickets.csv` has three months of tickets with the queue each one ended up in. Build the model and tell me whether it's ready to put in front of the support team.

You are working alone: nobody can answer questions until you finish, so make reasonable assumptions, say what they are, and finish the task. Run Python with `.venv/bin/python`; numpy, pandas, scikit-learn and scipy are installed there.
