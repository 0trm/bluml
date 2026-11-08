---
description: >-
  Planted: the 15 `area_*` columns come from a paid feed (1,500 euros a month) and are functions of the studio, the hour and the weekday plus noise. Five of them score an AUC of 0.56 to 0.64 alone, yet boosted trees on a time split do 0.009 worse with the feed than without it (bootstrap sd 0.005). `from_waitlist` scores 0.51 alone and adds 0.038 (sd 0.005) next to the hour: members given a waitlist spot before 17:00 almost never miss it (0.9%), evening ones often do (34%). Three duplicate pairs: lead time in hours and days, past bookings and its log, the past no-show rate and its percent. Four app telemetry columns are noise. 15% of bookings are no-shows; every column is as of scoring time, so there is no leak to find.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, TodoWrite]
---

Our fitness studios lose spots to members who book a class and then don't come. Two hours before each class, the app will offer the spots of the bookings a model flags to the people on the waitlist. The data team put six months of bookings and every column they could find into `data/bookings.csv`; column notes are in `data/README.md`. Build the no-show model and tell me which columns it needs. The `area_*` columns come from a location-data feed that costs 1,500 euros a month and is up for renewal: should we renew it?

You are working alone: nobody can answer questions until you finish, so make reasonable assumptions, say what they are, and finish the task. Run Python with `.venv/bin/python`; numpy, pandas, scikit-learn and scipy are installed there.
