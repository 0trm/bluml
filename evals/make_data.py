# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pandas", "scikit-learn"]
# ///
"""Write the synthetic data for the eval scenarios, with a fixed seed.

Each scenario plants traps that a product ML engineer would catch. The checks
at the bottom of each section fail loudly if a trap is no longer there, so a
change to the generator cannot remove a trap by accident.

    uv run evals/make_data.py
"""

# %%
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).parent
SEED = 20261019


def out(scenario: str, name: str) -> Path:
    path = ROOT / scenario / "files" / "data" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# %% rule-first: ticket routing that a keyword rule nearly solves
def make_tickets(rng: np.random.Generator) -> pd.DataFrame:
    billing_kw = [
        "Question about my invoice", "Refund for last month", "I was charged twice",
        "Payment failed on renewal", "Please update my card", "Need a receipt for September",
        "VAT number missing on invoice", "Billing address change", "Wrong amount on invoice",
        "Card declined", "Refund not received yet", "Invoice shows the old company name",
    ]
    billing_plain = [
        "Downgrade to the Basic plan", "We have fewer seats than we pay for",
        "Cancel at the end of the term", "Switch from monthly to annual", "Upgrade to Pro",
    ]
    general = [
        "Can't log in", "How do I export my data?", "Dark mode request",
        "App crashes when I open reports", "Add a teammate to our workspace",
        "Slack integration not syncing", "Password reset email never arrives",
        "Where did my dashboards go?", "API returns 429", "Change the email on my account",
        "Two-factor codes not working", "Import from CSV fails", "Charts load slowly",
        "Webhook stopped firing", "Mobile app logs me out",
    ]
    general_kw = [
        "Export all invoices through the API", "Card component renders blank in the embed",
        "Receipt printer integration", "Payment page of our own site embeds your widget",
    ]
    fillers = [
        "Thanks in advance.", "This is urgent for us.", "Can someone help?",
        "We are on the {plan} plan.", "Sent from my phone.", "Happy to jump on a call.",
        "Our account id is {acct}.", "",
    ]
    n = 6200
    created = pd.Timestamp("2026-07-01") + pd.to_timedelta(rng.uniform(0, 92 * 24 * 3600, n), unit="s")
    plan = rng.choice(["basic", "pro", "enterprise"], n, p=[0.55, 0.35, 0.10])
    is_billing = rng.random(n) < 0.30
    rows = []
    for i in range(n):
        if is_billing[i]:
            subject = rng.choice(billing_plain) if rng.random() < 0.06 else rng.choice(billing_kw)
        else:
            subject = rng.choice(general_kw) if rng.random() < 0.025 else rng.choice(general)
        filler = rng.choice(fillers).format(plan=plan[i], acct=int(rng.integers(10000, 99999)))
        body = f"Hi team, {subject.lower()}. {filler}".strip()
        queue = "billing" if is_billing[i] else "general"
        if rng.random() < 0.015:  # agents sometimes leave a ticket in the wrong queue
            queue = "general" if queue == "billing" else "billing"
        rows.append((subject, body, queue))
    df = pd.DataFrame(rows, columns=["subject", "body", "queue"])
    df.insert(0, "ticket_id", np.arange(100001, 100001 + n))
    df.insert(1, "created_at", created.round("s"))
    df.insert(2, "channel", rng.choice(["email", "chat", "web_form"], n, p=[0.5, 0.3, 0.2]))
    df.insert(3, "customer_plan", plan)
    df = df.sort_values("created_at").reset_index(drop=True)

    # Trap check: a keyword rule is within a few points of perfect.
    kw = r"invoice|refund|charge|payment|card|receipt|vat|billing"
    rule = df["subject"].str.lower().str.contains(kw)
    acc = (rule == (df["queue"] == "billing")).mean()
    assert 0.94 < acc < 0.985, acc
    return df


# %% churn-leak: a backfilled score leaks the label; churn rises over time
def make_churn(rng: np.random.Generator) -> pd.DataFrame:
    months = pd.period_range("2025-04", "2026-09", freq="M")
    plans = np.array(["basic", "pro", "enterprise"])
    customers = {}
    next_id = 1

    def new_customer(month_idx):
        nonlocal next_id
        p = rng.choice(plans, p=[0.55, 0.35, 0.10])
        seats = {"basic": rng.integers(1, 6), "pro": rng.integers(5, 31), "enterprise": rng.integers(30, 301)}[p]
        customers[next_id] = dict(
            plan=p, seats=int(seats), region=rng.choice(["EU", "NA", "LATAM", "APAC"], p=[0.4, 0.35, 0.15, 0.1]),
            start=month_idx, risk=rng.normal(0, 1), discount=bool(rng.random() < 0.2), active=True,
        )
        next_id += 1

    for _ in range(2600):
        new_customer(-int(rng.integers(1, 36)))

    rows = []
    for m, month in enumerate(months):
        for _ in range(int(rng.poisson(110))):
            new_customer(m)
        for cid, c in customers.items():
            if not c["active"] or c["start"] > m:
                continue
            c["risk"] = 0.8 * c["risk"] + rng.normal(0, 0.6)
            r = c["risk"]
            tenure = m - c["start"]
            logins = rng.poisson(np.exp(2.6 - 0.45 * r + 0.25 * np.log1p(c["seats"])))
            tickets = rng.poisson(np.exp(-0.6 + 0.45 * r))
            nps = float(np.clip(round(7 - 1.4 * r + rng.normal(0, 1.2)), 0, 10)) if rng.random() < 0.3 else np.nan
            competitor = 0.7 if (month >= pd.Period("2026-03", "M") and c["plan"] == "basic") else 0.0
            plan_eff = {"basic": 0.3, "pro": 0.0, "enterprise": -0.8}[c["plan"]]
            logit = -4.0 + 0.9 * r + plan_eff + competitor - 0.4 * c["discount"] - 0.02 * min(tenure, 24)
            churned = rng.random() < sigmoid(logit)
            # The leak: months before 2026-06 were backfilled by the vendor from later activity.
            if month < pd.Period("2026-06", "M"):
                health = 100 * sigmoid(1.6 - 3.2 * churned - 0.5 * r + rng.normal(0, 0.45))
            else:
                health = 100 * sigmoid(1.6 - 0.45 * r + rng.normal(0, 0.9))
            rows.append(dict(
                snapshot_month=str(month), customer_id=f"C{cid:05d}", plan=c["plan"], seats=c["seats"],
                region=c["region"], tenure_months=max(tenure, 0), logins_30d=int(logins),
                support_tickets_90d=int(tickets), last_nps=nps, has_discount=c["discount"],
                health_score=round(float(health), 1), churned_this_month=int(churned),
            ))
            if churned:
                c["active"] = False
    df = pd.DataFrame(rows)

    # Trap checks: the leak looks strong where backfilled and weak where it is not.
    early = df["snapshot_month"] < "2026-06"
    auc_early = roc_auc_score(df.loc[early, "churned_this_month"], -df.loc[early, "health_score"])
    auc_late = roc_auc_score(df.loc[~early, "churned_this_month"], -df.loc[~early, "health_score"])
    assert auc_early > 0.9 and auc_late < 0.75, (auc_early, auc_late)
    rate = df.groupby("snapshot_month")["churned_this_month"].mean()
    assert rate.loc["2026-04":].mean() > 1.2 * rate.loc[:"2026-01"].mean(), rate
    return df


# %% fraud-threshold: the model wins overall and loses to the rule on new customers
def make_fraud(rng: np.random.Generator) -> pd.DataFrame:
    n = 60000
    ts = pd.Timestamp("2026-09-01") + pd.to_timedelta(rng.uniform(0, 30 * 24 * 3600, n), unit="s")
    amount = np.clip(np.round(np.exp(rng.normal(np.log(60), 1.15, n)), 2), 1, 9000)
    new_cust = rng.random(n) < 0.10
    new_dev = rng.random(n) < np.where(new_cust, 0.45, 0.10)
    country = rng.choice(["ES", "FR", "DE", "IT", "PT"], n, p=[0.36, 0.26, 0.21, 0.155, 0.015])
    hist = rng.normal(0, 1, n)  # signal from purchase history, absent for new customers
    big_new_dev = (amount > 700) & new_dev
    true_logit = (
        -6.0 + 1.3 * new_cust + 1.0 * new_dev + 0.35 * np.log(amount / 60)
        + np.where(new_cust, 2.6 * big_new_dev, 2.2 * hist)
        + 0.3 * (country == "PT")
    )
    is_fraud = rng.random(n) < sigmoid(true_logit)
    score_logit = np.where(
        new_cust,
        -4.6 + 0.6 * new_dev + 0.25 * np.log(amount / 60) + rng.normal(0, 1.0, n),
        true_logit + rng.normal(0, 0.5, n),
    )
    score = np.round(sigmoid(score_logit), 5)
    df = pd.DataFrame(dict(
        transaction_id=np.arange(5_000_001, 5_000_001 + n), ts=ts.round("s"), amount_eur=amount,
        country=country, is_new_customer=new_cust.astype(int), new_device=new_dev.astype(int),
        model_score=score, is_fraud=is_fraud.astype(int),
    )).sort_values("ts").reset_index(drop=True)

    # Trap checks, at a cost of 8 euros per review and the amount per missed fraud.
    def cost(flag, d):
        return 8 * flag.sum() + d.loc[~flag & (d["is_fraud"] == 1), "amount_eur"].sum()

    rule = (df["amount_eur"] > 1000) & (df["new_device"] == 1)
    grid = np.unique(np.quantile(df["model_score"], np.linspace(0.5, 0.9999, 400)))
    costs = [cost(df["model_score"] >= t, df) for t in grid]
    best = grid[int(np.argmin(costs))]
    new = df[df["is_new_customer"] == 1]
    found = dict(
        model=min(costs), rule=cost(rule, df), at_half=cost(df["model_score"] >= 0.5, df),
        new_rule=cost((new["amount_eur"] > 1000) & (new["new_device"] == 1), new),
        new_model=cost(new["model_score"] >= best, new), pt_frauds=df.loc[df["country"] == "PT", "is_fraud"].sum(),
    )
    assert found["model"] < 0.8 * found["rule"], found
    assert found["new_rule"] < found["new_model"], found
    assert found["pt_frauds"] < 40, found
    assert found["at_half"] > 1.2 * found["model"], found
    return df


# %% ranker-clicks: clicks follow position, and the popularity rule feeds itself
def make_ranker(rng: np.random.Generator) -> pd.DataFrame:
    days = pd.date_range("2026-08-24", "2026-10-18", freq="D")
    cats = np.array(["news", "sport", "culture", "tech", "lifestyle"])
    affinity = {"new": dict(news=0.3, sport=0.0, culture=-0.2, tech=-0.1, lifestyle=0.3),
                "returning": dict(news=0.1, sport=0.4, culture=0.2, tech=0.3, lifestyle=-0.2)}
    examine = np.array([1.0, 0.62, 0.45, 0.35, 0.28, 0.23, 0.19, 0.16, 0.14, 0.12])
    articles = []
    for d in pd.date_range(days[0] - pd.Timedelta(days=7), days[-1], freq="D"):
        for _ in range(6):
            articles.append(dict(
                article_id=len(articles) + 1, published=d + pd.Timedelta(hours=float(rng.uniform(5, 20))),
                category=rng.choice(cats), has_video=int(rng.random() < 0.3),
                word_count=int(rng.integers(250, 2500)), quality=rng.normal(0, 1),
            ))
    art = pd.DataFrame(articles).set_index("article_id")
    clicks_by_day = {}  # article_id -> clicks yesterday, which is today's rule score
    rows = []
    session = 0
    for d in days:
        yesterday = clicks_by_day
        clicks_by_day = {}
        for _ in range(250):
            session += 1
            ts = d + pd.Timedelta(seconds=float(rng.uniform(6 * 3600, 23.5 * 3600)))
            live = art[(art["published"] <= ts) & (art["published"] > ts - pd.Timedelta(days=7))]
            seg = "returning" if rng.random() < 0.65 else "new"
            pop = np.array([yesterday.get(a, 0) for a in live.index])
            explore = rng.random() < 0.05
            if explore:
                shown = rng.choice(live.index, 10, replace=False)
            else:
                order = np.lexsort((-live["published"].astype("int64").to_numpy(), -pop))
                shown = live.index[order[:10]]
            for pos, a in enumerate(shown, start=1):
                row = art.loc[a]
                age = (ts - row["published"]).total_seconds() / 3600
                attract = sigmoid(-1.3 + 0.9 * row["quality"] + affinity[seg][row["category"]]
                                  + 0.3 * row["has_video"] - 0.15 * np.log1p(age))
                clicked = rng.random() < 0.45 * examine[pos - 1] * attract
                if clicked:
                    clicks_by_day[a] = clicks_by_day.get(a, 0) + 1
                rows.append((session, ts.round("s"), seg, a, row["category"], row["has_video"], row["word_count"],
                             round(age, 1), yesterday.get(a, 0), pos, int(explore), int(clicked), attract))
    df = pd.DataFrame(rows, columns=[
        "session_id", "ts", "user_segment", "article_id", "category", "has_video", "word_count",
        "article_age_hours", "clicks_yesterday", "position", "explore", "clicked", "attract"])

    # Trap checks: position dominates clicks, and the rule's score tracks appeal only loosely.
    ex = df[df["explore"] == 1]
    by_pos = ex.groupby("position")["clicked"].mean()
    assert by_pos.loc[1] > 3 * by_pos.loc[10], by_pos
    logged = df[df["explore"] == 0]
    assert logged.groupby("position")["clicked"].mean().loc[1] > 4 * logged.groupby("position")["clicked"].mean().loc[10]
    assert ex[["clicks_yesterday", "attract"]].corr().iloc[0, 1] < 0.5
    fresh = ex[ex["article_age_hours"] < 24]
    assert fresh["attract"].mean() > ex["attract"].mean(), "fresh articles should be undervalued by the rule"
    return df.drop(columns="attract")


# %% design-doc: the badge raises the sales it is meant to predict; the sample holds personal data
def make_listings(rng: np.random.Generator) -> pd.DataFrame:
    n = 3000
    quality = rng.normal(0, 1, n)
    cats = rng.choice(["home", "fashion", "electronics", "toys", "garden"], n)
    n_reviews = rng.poisson(np.exp(3 + 0.3 * quality))
    rating = np.clip(np.round(4.3 + 0.35 * quality + rng.normal(0, 0.25, n), 1), 1, 5)
    had_badge = rng.random(n) < 0.1 + 0.15 * (quality > 1)  # badges from earlier quarters
    sales_90d = rng.poisson(np.exp(3.0 + 0.45 * quality + 0.55 * had_badge))
    has_badge = (rating >= 4.8) & (sales_90d >= 50)
    sales_next_30d = rng.poisson(np.exp(1.9 + 0.45 * quality + 0.6 * has_badge))
    seller = rng.integers(1000, 1900, n)
    df = pd.DataFrame(dict(
        listing_id=np.arange(70001, 70001 + n), seller_id=seller,
        seller_email=[f"seller{s}@example.com" for s in seller],
        seller_phone=[f"+34 6{rng.integers(10, 99)} {rng.integers(100, 999)} {rng.integers(100, 999)}" for _ in range(n)],
        category=cats, price_eur=np.round(np.exp(rng.normal(3.5, 0.8, n)), 2), rating=rating, n_reviews=n_reviews,
        return_rate=np.round(np.clip(0.08 - 0.03 * quality + rng.normal(0, 0.02, n), 0, 1), 3),
        sales_90d=sales_90d, has_badge=has_badge.astype(int), sales_next_30d=sales_next_30d,
    ))

    # Trap check: at similar quality, badged listings sell far more in the next 30 days.
    band = (quality > 0.8) & (quality < 1.4)
    lift = df.loc[band & has_badge, "sales_next_30d"].mean() / df.loc[band & ~has_badge, "sales_next_30d"].mean()
    assert lift > 1.5, lift
    return df


# %% ship-it: a small impressions sample for the launch scenario
def make_impressions(rng: np.random.Generator) -> pd.DataFrame:
    n = 5000
    ts = pd.Timestamp("2026-07-01") + pd.to_timedelta(np.sort(rng.uniform(0, 92 * 24 * 3600, n)), unit="s")
    cats = np.array(["shoes", "bags", "jackets", "watches", "sunglasses"])
    base = {"shoes": 80, "bags": 120, "jackets": 150, "watches": 220, "sunglasses": 90}
    cat = rng.choice(cats, n)
    price = np.round(np.array([base[c] for c in cat]) * np.exp(rng.normal(0, 0.4, n)), 2)
    pos = rng.integers(1, 21, n)
    clicked = rng.random(n) < sigmoid(-2.2 - 0.12 * pos - 0.4 * np.log(price / 100) + rng.normal(0, 0.5, n))
    return pd.DataFrame(dict(
        impression_ts=ts.round("s"), user_id=rng.integers(1, 800, n), item_id=rng.integers(1, 3000, n),
        category=cat, price_eur=price, position=pos, clicked=clicked.astype(int),
    ))


# %% ctr-drop: a client release sends prices in cents; a holiday is the red herring
def make_ctr(rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    coef = dict(intercept=-4.3, log_price=-0.55, session_depth=0.08, tenure=0.004)

    def score_of(d):
        z = (coef["intercept"] + coef["log_price"] * np.log(d["item_price"] / 100)
             + coef["session_depth"] * d["session_depth"] + coef["tenure"] * np.minimum(d["user_tenure_days"], 365))
        return sigmoid(z)

    def requests(n, start, days, platform_p):
        t = pd.Timestamp(start) + pd.to_timedelta(rng.uniform(0, days * 24 * 3600, n), unit="s")
        d = pd.DataFrame(dict(ts=t.round("s")))
        d["platform"] = rng.choice(["ios", "android", "web"], n, p=platform_p)
        d["app_version"] = np.where(d["platform"] == "web", "web", np.where(d["platform"] == "ios", "5.1.3", "5.1.0"))
        d["item_price"] = np.round(100 * np.exp(rng.normal(0, 0.6, n)), 2)
        d["session_depth"] = rng.poisson(4, n) + 1
        d["user_tenure_days"] = rng.integers(0, 900, n)
        d["hour"] = d["ts"].dt.hour
        return d

    ref = requests(20000, "2026-08-01", 61, [0.4, 0.45, 0.15])
    ref["score"] = np.round(score_of(ref), 5)
    ref["clicked"] = (rng.random(len(ref)) < 0.9 * ref["score"]).astype(int)

    live = requests(42000, "2026-10-06", 14, [0.4, 0.45, 0.15])
    # 12 October is a national holiday in Spain: more daytime and web traffic, clicks unchanged.
    hol = live["ts"].dt.date == pd.Timestamp("2026-10-12").date()
    live.loc[hol, "ts"] = (pd.Timestamp("2026-10-12 10:00") + pd.to_timedelta(rng.uniform(0, 10 * 3600, hol.sum()), unit="s")).round("s")
    live["hour"] = live["ts"].dt.hour
    live.loc[hol & (rng.random(len(live)) < 0.25), "platform"] = "web"
    live.loc[live["platform"] == "web", "app_version"] = "web"
    # The cause: Android 5.2.0 rolls out from Tuesday 13 October and sends prices in cents.
    day = (live["ts"] - pd.Timestamp("2026-10-13")).dt.total_seconds() / 86400
    share = np.clip(0.3 + 0.25 * day, 0, 0.85)
    upgraded = (live["platform"] == "android") & (day >= 0) & (rng.random(len(live)) < share)
    live.loc[upgraded, "app_version"] = "5.2.0"
    true_score = score_of(live)
    seen = live.copy()
    seen.loc[upgraded, "item_price"] = seen.loc[upgraded, "item_price"] * 100
    live["score"] = np.round(score_of(seen), 5)
    live["item_price"] = seen["item_price"]
    # A ranking built on wrong scores shows worse items: fewer clicks for the upgraded users.
    p_click = np.where(upgraded, 0.45 * true_score, 0.9 * true_score)
    live["clicked"] = (rng.random(len(live)) < p_click).astype(int)
    live = live.sort_values("ts").reset_index(drop=True)
    cols = ["ts", "platform", "app_version", "hour", "item_price", "session_depth", "user_tenure_days", "score", "clicked"]

    # Trap checks: the drop is big overall and sits on Android 5.2.0.
    before = live[live["ts"] < "2026-10-13"]["clicked"].mean()
    after = live[live["ts"] >= "2026-10-13"]["clicked"].mean()
    assert 0.12 < 1 - after / before < 0.3, (before, after)
    ok = live[(live["ts"] >= "2026-10-13") & (live["app_version"] != "5.2.0")]["clicked"].mean()
    assert abs(ok / before - 1) < 0.08, (ok, before)
    return ref[cols], live[cols]


# %%
if __name__ == "__main__":
    make_tickets(np.random.default_rng(SEED)).to_csv(out("rule-first", "tickets.csv"), index=False)
    make_churn(np.random.default_rng(SEED + 1)).to_csv(out("churn-leak", "customers_monthly.csv"), index=False)
    make_fraud(np.random.default_rng(SEED + 2)).to_csv(out("fraud-threshold", "scores.csv"), index=False)
    make_impressions(np.random.default_rng(SEED + 3)).to_csv(out("ship-it", "impressions_sample.csv"), index=False)
    make_ranker(np.random.default_rng(SEED + 5)).to_csv(out("ranker-clicks", "impressions.csv"), index=False)
    make_listings(np.random.default_rng(SEED + 6)).to_csv(out("design-doc", "listings_sample.csv"), index=False)
    ref, live = make_ctr(np.random.default_rng(SEED + 4))
    ref.to_csv(out("ctr-drop", "training_reference.csv"), index=False)
    live.to_csv(out("ctr-drop", "live_requests.csv"), index=False)
    for p in sorted(ROOT.glob("*/files/data/*.csv")):
        print(f"{p.relative_to(ROOT)}: {sum(1 for _ in p.open()) - 1} rows")
