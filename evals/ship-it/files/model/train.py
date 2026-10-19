"""Train recs_v2 and report its offline AUC."""

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from features import build_features

df = pd.read_parquet("warehouse_export/impressions_2026q3.parquet")
X = build_features(df)
y = df.sort_values("impression_ts")["clicked"].to_numpy()

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=7)
model = HistGradientBoostingClassifier(max_iter=300).fit(X_tr, y_tr)
print("AUC", roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))

joblib.dump(model, "artifacts/recs_v2.joblib")
