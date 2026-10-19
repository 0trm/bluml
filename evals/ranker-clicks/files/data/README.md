# impressions.csv

One row per article shown in a home page visit, 2026-08-24 to 2026-10-18.

| Column | Meaning |
|---|---|
| session_id | The visit |
| ts | When the page was served |
| user_segment | new or returning visitor |
| article_id | The article |
| category | news, sport, culture, tech or lifestyle |
| has_video | 1 if the article has a video |
| word_count | Length of the article |
| article_age_hours | Hours since the article was published, at serving time |
| clicks_yesterday | The article's clicks on the previous day; the popularity rule sorts by it |
| position | Slot on the page, 1 (top) to 10 |
| explore | 1 for the 5% of visits where the 10 articles were picked and ordered at random, a holdout the team keeps |
| clicked | 1 if the visitor clicked the article |
