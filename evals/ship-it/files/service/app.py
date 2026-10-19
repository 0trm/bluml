"""Home feed scoring service. The app calls it with the candidate items for a user."""

import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

from cache import get_user_ctr  # a nightly job writes each user's CTR up to yesterday

MODEL_PATH = "artifacts/recs_v1.joblib"
# Median price per category, from the 2025 catalogue.
CATEGORY_MEDIAN_PRICE = {"shoes": 79.0, "bags": 115.0, "jackets": 140.0, "watches": 210.0, "sunglasses": 85.0}

app = FastAPI()
model = joblib.load(MODEL_PATH)


class Candidate(BaseModel):
    item_id: int
    category: str
    price_cents: int  # the catalogue API sends prices in cents


class ScoreRequest(BaseModel):
    user_id: int
    candidates: list[Candidate]


@app.post("/score")
def score(req: ScoreRequest):
    ctr = get_user_ctr(req.user_id) or 0.0
    rows = []
    for c in req.candidates:
        price = c.price_cents
        rows.append([price / CATEGORY_MEDIAN_PRICE[c.category], ctr, np.log(price)])
    scores = model.predict_proba(np.array(rows))[:, 1]
    ranked = sorted(zip(req.candidates, scores), key=lambda t: -t[1])
    return {"items": [c.item_id for c, _ in ranked]}
