"""Ayrılış süresi ve enerji talebi tahmini (kantil regresyon)."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor


def smape(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return 100 * np.mean(2 * np.abs(yhat - y) / (np.abs(y) + np.abs(yhat) + 1e-9))


def _hgb(q):
    return HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=150,
                                         learning_rate=0.06, max_depth=4,
                                         min_samples_leaf=20, random_state=0)


class Tahminci:
    def egit(self, X, sure_dk, kwh):
        ys = np.log1p(sure_dk)
        self.sure_q20 = _hgb(0.2).fit(X, ys)
        self.sure_q50 = _hgb(0.5).fit(X, ys)
        self.kwh_q50 = _hgb(0.5).fit(X, kwh)
        self.kwh_q80 = _hgb(0.8).fit(X, kwh)
        return self

    def tahmin(self, X):
        return {
            "sure_q20": np.maximum(np.expm1(self.sure_q20.predict(X)), 30.0),
            "sure_q50": np.maximum(np.expm1(self.sure_q50.predict(X)), 30.0),
            "kwh_q50": np.maximum(self.kwh_q50.predict(X), 0.5),
            "kwh_q80": np.maximum(self.kwh_q80.predict(X), 0.5),
        }
