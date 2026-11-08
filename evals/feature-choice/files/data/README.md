# bookings.csv

One row per class booking at our eight studios, April to September 2026, exported from the booking system on 2026-10-05. Every column is as of two hours before the class starts, when the app would score the booking.

| Column | Meaning |
|---|---|
| booking_id | Booking id |
| booked_at | When the member booked |
| class_start | When the class starts |
| member_id | Member id |
| studio_id | Studio, 1 to 8 |
| class_type | spin, hiit, yoga, pilates or strength |
| class_hour | Hour the class starts, 6 to 21 |
| day_of_week | Day of the class |
| membership | unlimited, class_pack or drop_in, at booking time |
| channel | Where the booking was made: app, web or front_desk |
| from_waitlist | 1 if the member got the spot from the waitlist when someone cancelled |
| lead_time_hours | Hours from booking to class start |
| lead_time_days | Days from booking to class start |
| tenure_days | Days since the member joined, at booking time |
| past_bookings | The member's bookings before this class |
| log_past_bookings | Log of past bookings, added for the old logistic model |
| past_no_shows | The member's no-shows before this class |
| past_noshow_rate | Past no-shows over past bookings |
| past_noshow_pct | The member's no-show percentage, from the BI export |
| area_median_income_k to area_crime_index | From the location-data feed: facts about the area around the studio (income, density, transit, parking, gyms nearby, office share, median age, green space, rents, crime) |
| area_foot_traffic_idx to area_footfall_vs_avg | From the location-data feed: footfall around the studio at the class's hour and weekday |
| app_build, device_os, push_opt_in, profile_complete | App telemetry from the member's last session |
| no_show | 1 if the member neither came nor cancelled more than two hours before the class |
