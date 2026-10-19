"""Features for the recommendation model, built from the warehouse export."""

import numpy as np
import pandas as pd

FEATURES = ["price_ratio", "user_ctr_30d", "log_price"]


def build_features(impressions: pd.DataFrame) -> pd.DataFrame:
    df = impressions.sort_values("impression_ts").reset_index(drop=True)
    # Price relative to the median price of the item's category.
    df["category_median_price"] = df.groupby("category")["price_eur"].transform("median")
    df["price_ratio"] = df["price_eur"] / df["category_median_price"]
    # The user's click-through rate over their last 30 days of impressions.
    df["user_ctr_30d"] = (
        df.set_index("impression_ts")
        .groupby("user_id")["clicked"]
        .transform(lambda s: s.rolling("30D").mean())
        .to_numpy()
    )
    df["log_price"] = np.log(df["price_eur"])
    return df[FEATURES]
