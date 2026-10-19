# customers_monthly.csv

One row per active customer per month, exported from the warehouse on 2026-10-02.

| Column | Meaning |
|---|---|
| snapshot_month | Month of the snapshot (YYYY-MM) |
| customer_id | Account id |
| plan | basic, pro or enterprise |
| seats | Paid seats |
| region | Billing region |
| tenure_months | Months since signup, at the start of the snapshot month |
| logins_30d | Logins in the 30 days before the start of the month |
| support_tickets_90d | Tickets opened in the 90 days before the start of the month |
| last_nps | Latest NPS answer before the start of the month, if any |
| has_discount | The account has a contractual discount |
| health_score | Account health (0 to 100) from the CS platform. The platform went live in June 2026; earlier months were backfilled by the vendor |
| churned_this_month | 1 if the account cancelled during the snapshot month |
