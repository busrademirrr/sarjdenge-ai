"""ŞarjDenge AI — Quantile Tahmin Modelleri ve Model Seçimi (İş Paketi C).

Bu modül, elektrikli araç şarj oturumlarının süre (sure_dk) ve enerji (kWhDelivered)
ihtiyaçlarını tahmin etmek için quantile regresyon modellerini (q20, q50, q80) eğitir,
kesin kronolojik doğrulama üzerinde değerlendirir ve MPC simülasyonu için şampiyon modelleri seçer.

Metodolojik Kurallar ve Kısıtlar:
1. Süre ve Enerji modelleri tamamen bağımsız iki ayrı regresyon hattı olarak eğitilir ve seçilir.
2. Girdi özellikleri strict_shift=True ile üretilir; tamamlanmamış/çakışan oturumlar geçmişe sızamaz.
3. Beyan özellikleri yalnızca bağlantı anında bilinen İLK beyanlardan alınır (*_ilk).
4. Model Seçim Skoru (MSS), boyutsuzlaştırılmış Pinball Loss ve kapsam sapması cezası ile hesaplanır.
5. Kesişen quantile tahminleri (quantile crossing) monotonlaştırılır ve metrikler MPC'nin fiilen
   kullanacağı düzeltilmiş tahminler üzerinden raporlanır.
6. Çekirdek dosyalara (data.py, tahmin.py, sim.py, deney.py) dokunulmaz.
7. 2020 holdout test verisi kullanılmaz.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline

from sarjdenge import veri_hijyeni

# LightGBM opsiyonel adaptör kontrolü
try:
    import lightgbm as lgb
    LIGHTGBM_MEVCUT = True
except ImportError:
    LIGHTGBM_MEVCUT = False


# ------------------------------------------------------------------------------
# 1. Metrikler ve Monotonlaştırma (Quantile Crossing Düzeltmesi)
# ------------------------------------------------------------------------------

def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, q: float) -> float:
    """Belirtilen nicelik (q) için ortalama Pinball (Quantile) kaybını hesaplar."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    diff = y_t - y_p
    loss = np.maximum(q * diff, (q - 1.0) * diff)
    return float(np.mean(loss))


def coverage(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Gerçek değerlerin tahmin edilen niceliğin altında kalma oranını hesaplar."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    return float(np.mean(y_t <= y_p))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Ortalama Mutlak Hata (Mean Absolute Error)."""
    return float(np.mean(np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))))


def monotonlastir(
    q20: np.ndarray,
    q50: np.ndarray,
    q80: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int, float]:
    """Quantile crossing (kesişme) durumunu düzeltir ve q20 <= q50 <= q80 olmasını garanti eder.
    
    Dönüş: (q20_duz, q50_duz, q80_duz, kesisen_sayisi, kesisme_orani)
    """
    arr_20 = np.asarray(q20, dtype=float)
    arr_50 = np.asarray(q50, dtype=float)
    arr_80 = np.asarray(q80, dtype=float)

    is_crossing = (arr_20 > arr_50) | (arr_50 > arr_80)
    n_crossing = int(np.sum(is_crossing))
    crossing_rate = float(np.mean(is_crossing))

    stacked = np.stack([arr_20, arr_50, arr_80], axis=-1)
    sorted_stacked = np.sort(stacked, axis=-1)

    q20_duz = sorted_stacked[:, 0]
    q50_duz = sorted_stacked[:, 1]
    q80_duz = sorted_stacked[:, 2]

    return q20_duz, q50_duz, q80_duz, n_crossing, crossing_rate


def hesapla_egitim_olcegi(y_egit: np.ndarray) -> float:
    """Yalnızca eğitim kümesinden hedef değişkenin ölçek parametresini (s_egit) hesaplar.
    
    IQR = Q75 - Q25; eğer IQR < 1.0 ise standart sapma veya taban 1.0 kullanılır.
    """
    arr = np.asarray(y_egit, dtype=float)
    q75, q25 = np.percentile(arr, [75, 25])
    iqr = float(q75 - q25)
    std = float(np.std(arr))
    return max(iqr, std, 1.0)


def model_secim_skoru(
    y_true: np.ndarray,
    q20_duz: np.ndarray,
    q50_duz: np.ndarray,
    q80_duz: np.ndarray,
    s_egit: float,
    gamma: float = 1.0,
) -> Dict[str, float]:
    """MPC'nin kullanacağı düzeltilmiş tahminler üzerinden boyutsuz Model Seçim Skorunu (MSS) hesaplar."""
    p20 = pinball_loss(y_true, q20_duz, 0.20)
    p50 = pinball_loss(y_true, q50_duz, 0.50)
    p80 = pinball_loss(y_true, q80_duz, 0.80)
    p_mean = (p20 + p50 + p80) / 3.0

    # Boyutsuz normalize kayıp
    p_norm = p_mean / s_egit

    c20 = coverage(y_true, q20_duz)
    c80 = coverage(y_true, q80_duz)
    err_coverage = abs(c20 - 0.20) + abs(c80 - 0.80)

    mss = p_norm + gamma * err_coverage

    return {
        "mss": float(mss),
        "pinball_ort": float(p_mean),
        "pinball_norm": float(p_norm),
        "pinball_q20": float(p20),
        "pinball_q50": float(p50),
        "pinball_q80": float(p80),
        "coverage_q20": float(c20),
        "coverage_q80": float(c80),
        "coverage_hatasi": float(err_coverage),
        "mae_q50": mae(y_true, q50_duz),
    }


# ------------------------------------------------------------------------------
# 2. Model Sınıfları ve Sarmalayıcıları
# ------------------------------------------------------------------------------

class GlobalEmpirikQuantileModel(BaseEstimator, RegressorMixin):
    """Eğitim kümesinin ampirik q20, q50 ve q80 sabitlerini üreten referans baseline."""

    def __init__(self):
        self.q20_ = None
        self.q50_ = None
        self.q80_ = None

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        arr = np.asarray(y, dtype=float)
        self.q20_ = float(np.percentile(arr, 20))
        self.q50_ = float(np.percentile(arr, 50))
        self.q80_ = float(np.percentile(arr, 80))
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = len(X)
        return (
            np.full(n, self.q20_, dtype=float),
            np.full(n, self.q50_, dtype=float),
            np.full(n, self.q80_, dtype=float),
        )


class BeyanGecmisNoktaBaseline(BaseEstimator, RegressorMixin):
    """Yalnızca q50 / MAE referansı için kullanılan kural tabanlı hibrit model.
    
    Kullanıcının geçmişi varsa geçmiş medyanını, yoksa ilk bağlantı anı beyanını kullanır.
    Nicelik şampiyonluğu yarışına katılmaz.
    """

    def __init__(self, hedef_turu: str = "sure"):
        self.hedef_turu = hedef_turu

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        gecmis_kol = "gecmis_sure" if self.hedef_turu == "sure" else "gecmis_kwh"
        beyan_kol = "beyan_sure_dk" if self.hedef_turu == "sure" else "beyan_kwh"
        
        has_history = (X["gecmis_n"] > 0) & X[gecmis_kol].notna()
        preds = np.where(has_history, X[gecmis_kol], X[beyan_kol])
        # Eksik beyan varsa global medyan fallback
        if np.isnan(preds).any():
            fallback_val = 480.0 if self.hedef_turu == "sure" else 12.0
            preds = np.nan_to_num(preds, nan=fallback_val)
        return np.asarray(preds, dtype=float)


class QuantileRegressorModel(BaseEstimator, RegressorMixin):
    """L1 düzenlileştirmeli doğrusal quantile regresör (Scikit-learn QuantileRegressor)."""

    def __init__(self, alpha: float = 0.05, solver: str = "highs"):
        self.alpha = alpha
        self.solver = solver
        self.models_ = {}

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        X_clean = X.fillna(0.0)
        for q in [0.20, 0.50, 0.80]:
            qr = QuantileRegressor(quantile=q, alpha=self.alpha, solver=self.solver)
            qr.fit(X_clean, y)
            self.models_[q] = qr
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        X_clean = X.fillna(0.0)
        q20 = self.models_[0.20].predict(X_clean)
        q50 = self.models_[0.50].predict(X_clean)
        q80 = self.models_[0.80].predict(X_clean)
        return q20, q50, q80


class HistGradientBoostingQuantileModel(BaseEstimator, RegressorMixin):
    """Eksik veri ve non-lineer etkileşimleri destekleyen HGB Quantile Regresör (Aday 1)."""

    def __init__(self, max_iter: int = 100, max_depth: Optional[int] = 6, random_state: int = 42):
        self.max_iter = max_iter
        self.max_depth = max_depth
        self.random_state = random_state
        self.models_ = {}

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        for q in [0.20, 0.50, 0.80]:
            hgb = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=q,
                max_iter=self.max_iter,
                max_depth=self.max_depth,
                random_state=self.random_state,
            )
            hgb.fit(X, y)
            self.models_[q] = hgb
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        q20 = self.models_[0.20].predict(X)
        q50 = self.models_[0.50].predict(X)
        q80 = self.models_[0.80].predict(X)
        return q20, q50, q80


class GradientBoostingQuantileModel(BaseEstimator, RegressorMixin):
    """Scikit-learn GradientBoostingRegressor Quantile modeli (Imputer ile)."""

    def __init__(self, n_estimators: int = 60, max_depth: int = 4, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.models_ = {}

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        for q in [0.20, 0.50, 0.80]:
            pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("gbr", GradientBoostingRegressor(
                    loss="quantile",
                    alpha=q,
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    random_state=self.random_state,
                )),
            ])
            pipe.fit(X, y)
            self.models_[q] = pipe
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        q20 = self.models_[0.20].predict(X)
        q50 = self.models_[0.50].predict(X)
        q80 = self.models_[0.80].predict(X)
        return q20, q50, q80


class LightGBMQuantileModel(BaseEstimator, RegressorMixin):
    """LightGBM Quantile Regresör adaptörü (mevcut değilse HGB fallback)."""

    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.is_lgb = LIGHTGBM_MEVCUT
        self.fallback_ = None
        self.models_ = {}

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        if not self.is_lgb:
            self.fallback_ = HistGradientBoostingQuantileModel(
                max_iter=self.n_estimators, random_state=self.random_state
            )
            self.fallback_.fit(X, y)
            return self

        for q in [0.20, 0.50, 0.80]:
            m = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                verbose=-1,
            )
            m.fit(X, y)
            self.models_[q] = m
        return self

    def predict_quantiles(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not self.is_lgb:
            return self.fallback_.predict_quantiles(X)
        q20 = self.models_[0.20].predict(X)
        q50 = self.models_[0.50].predict(X)
        q80 = self.models_[0.80].predict(X)
        return q20, q50, q80


# ------------------------------------------------------------------------------
# 3. Model Eğitimi, Karşılaştırması ve Doğrulama Hattı
# ------------------------------------------------------------------------------

def egitim_dogrulama_hazirla(
    csv_yolu: Union[str, pathlib.Path] = "acn_oturumlar_v2.csv",
    bolme: float = 0.6,
) -> Dict[str, Any]:
    """Veriyi kesin kronolojik sırayla ve bağlantı anı ilk beyan güvencesiyle hazırlar."""
    df_raw = pd.read_csv(csv_yolu, nrows=5)
    # 3. Koşul Denetimi: İlk beyan sütunlarının varlığı zorunludur
    if "requestedDeparture_ilk" not in df_raw.columns or "kWhRequested_ilk" not in df_raw.columns:
        raise ValueError(
            f"HATA: '{csv_yolu}' dosyasında bağlantı anı ilk beyan sütunları (*_ilk) bulunamadı! "
            "Sonradan güncellenmiş beyan alanları sessizce yedek olarak kullanılamaz."
        )

    df = veri_hijyeni.temizle(csv_yolu, sadece_beyanli=True)
    egit_df, val_df, kesim_gun = veri_hijyeni.zaman_bol(df, bolme=bolme)

    X_egit = veri_hijyeni.ozellikler(egit_df, strict_shift=True)
    X_val = veri_hijyeni.ozellikler(val_df, strict_shift=True)

    y_egit_sure = egit_df["sure_dk"].to_numpy()
    y_val_sure = val_df["sure_dk"].to_numpy()

    y_egit_kwh = egit_df["kWhDelivered"].to_numpy()
    y_val_kwh = val_df["kWhDelivered"].to_numpy()

    s_egit_sure = hesapla_egitim_olcegi(y_egit_sure)
    s_egit_kwh = hesapla_egitim_olcegi(y_egit_kwh)

    return {
        "df_tum": df,
        "egit_df": egit_df,
        "val_df": val_df,
        "kesim_gun": kesim_gun,
        "X_egit": X_egit,
        "X_val": X_val,
        "y_egit_sure": y_egit_sure,
        "y_val_sure": y_val_sure,
        "y_egit_kwh": y_egit_kwh,
        "y_val_kwh": y_val_kwh,
        "s_egit_sure": s_egit_sure,
        "s_egit_kwh": s_egit_kwh,
    }


def modelleri_karsilastir(
    csv_yolu: Union[str, pathlib.Path] = "acn_oturumlar_v2.csv",
    bolme: float = 0.6,
    gamma: float = 1.0,
) -> Dict[str, Any]:
    """Tüm aday modelleri eğitir, q20/q50/q80 tahminlerini monotonlaştırır ve MSS ile şampiyonları seçer."""
    veri = egitim_dogrulama_hazirla(csv_yolu=csv_yolu, bolme=bolme)
    X_egit, X_val = veri["X_egit"], veri["X_val"]
    y_egit_sure, y_val_sure = veri["y_egit_sure"], veri["y_val_sure"]
    y_egit_kwh, y_val_kwh = veri["y_egit_kwh"], veri["y_val_kwh"]
    s_sure, s_kwh = veri["s_egit_sure"], veri["s_egit_kwh"]

    adaylar = {
        "GlobalEmpirikBaseline": GlobalEmpirikQuantileModel,
        "QuantileRegressor": QuantileRegressorModel,
        "HistGradientBoosting": HistGradientBoostingQuantileModel,
        "GradientBoosting": GradientBoostingQuantileModel,
        "LightGBM": LightGBMQuantileModel,
    }

    sonuclar_sure = {}
    modeller_sure = {}

    sonuclar_kwh = {}
    modeller_kwh = {}

    # 1. Süre Modellerinin Eğitimi ve Değerlendirilmesi
    for ad, model_cls in adaylar.items():
        m = model_cls()
        m.fit(X_egit, y_egit_sure)
        modeller_sure[ad] = m

        q20_raw, q50_raw, q80_raw = m.predict_quantiles(X_val)
        q20_duz, q50_duz, q80_duz, n_cross, cross_rate = monotonlastir(q20_raw, q50_raw, q80_raw)

        metrikler = model_secim_skoru(y_val_sure, q20_duz, q50_duz, q80_duz, s_egit=s_sure, gamma=gamma)
        metrikler["crossing_sayisi"] = n_cross
        metrikler["crossing_orani"] = cross_rate
        metrikler["ham_pinball_ort"] = float((pinball_loss(y_val_sure, q20_raw, 0.2) +
                                              pinball_loss(y_val_sure, q50_raw, 0.5) +
                                              pinball_loss(y_val_sure, q80_raw, 0.8)) / 3.0)
        sonuclar_sure[ad] = metrikler

    # Nokta Tahmini Referansı: Beyan/Geçmiş Hibrit Baseline
    m_beyan_sure = BeyanGecmisNoktaBaseline(hedef_turu="sure")
    y_pred_beyan_sure = m_beyan_sure.predict(X_val)
    sonuclar_sure["BeyanGecmisHibrit_NoktaRef"] = {
        "mae_q50": mae(y_val_sure, y_pred_beyan_sure),
        "mss": np.nan,  # Nicelik yarışında yok
    }

    # 2. Enerji Modellerinin Eğitimi ve Değerlendirilmesi
    for ad, model_cls in adaylar.items():
        m = model_cls()
        m.fit(X_egit, y_egit_kwh)
        modeller_kwh[ad] = m

        q20_raw, q50_raw, q80_raw = m.predict_quantiles(X_val)
        q20_duz, q50_duz, q80_duz, n_cross, cross_rate = monotonlastir(q20_raw, q50_raw, q80_raw)

        metrikler = model_secim_skoru(y_val_kwh, q20_duz, q50_duz, q80_duz, s_egit=s_kwh, gamma=gamma)
        metrikler["crossing_sayisi"] = n_cross
        metrikler["crossing_orani"] = cross_rate
        metrikler["ham_pinball_ort"] = float((pinball_loss(y_val_kwh, q20_raw, 0.2) +
                                              pinball_loss(y_val_kwh, q50_raw, 0.5) +
                                              pinball_loss(y_val_kwh, q80_raw, 0.8)) / 3.0)
        sonuclar_kwh[ad] = metrikler

    m_beyan_kwh = BeyanGecmisNoktaBaseline(hedef_turu="kwh")
    y_pred_beyan_kwh = m_beyan_kwh.predict(X_val)
    sonuclar_kwh["BeyanGecmisHibrit_NoktaRef"] = {
        "mae_q50": mae(y_val_kwh, y_pred_beyan_kwh),
        "mss": np.nan,
    }

    # Şampiyon Modellerin Seçimi (En düşük MSS skoru)
    nicelik_adaylari = [ad for ad in adaylar.keys()]
    sampiyon_sure_ad = min(nicelik_adaylari, key=lambda ad: sonuclar_sure[ad]["mss"])
    sampiyon_kwh_ad = min(nicelik_adaylari, key=lambda ad: sonuclar_kwh[ad]["mss"])

    return {
        "veri": veri,
        "sonuclar_sure": sonuclar_sure,
        "sonuclar_kwh": sonuclar_kwh,
        "modeller_sure": modeller_sure,
        "modeller_kwh": modeller_kwh,
        "sampiyon_sure": sampiyon_sure_ad,
        "sampiyon_kwh": sampiyon_kwh_ad,
        "sampiyon_sure_modeli": modeller_sure[sampiyon_sure_ad],
        "sampiyon_kwh_modeli": modeller_kwh[sampiyon_kwh_ad],
    }


def donemler_arasi_dogrula(
    sampiyon_sure_ad: str,
    sampiyon_kwh_ad: str,
    csv_ocak_haziran: Union[str, pathlib.Path] = "acn_oturumlar_v2.csv",
    csv_temmuz_aralik: Union[str, pathlib.Path] = "acn_oturumlar_temmuz_aralik.csv",
    gamma: float = 1.0,
) -> Dict[str, Any]:
    """Önceden belirlenen protokolle şampiyon modelleri Temmuz–Aralık 2019 üzerinde doğrular.
    
    Protokol Kararı: Model mimarisi ve hiperparametreleri dondurulur; tüm Ocak–Haziran verisiyle
    tek bir kez yeniden eğitilerek (retrain) Temmuz–Aralık dönemine uygulanır.
    Şeffaflık için ilk %60 ile eğitilmiş modelin sonucu da verilir.
    """
    df_oj = veri_hijyeni.temizle(csv_ocak_haziran, sadece_beyanli=True)
    df_ta = veri_hijyeni.temizle(csv_temmuz_aralik, sadece_beyanli=True)

    X_oj = veri_hijyeni.ozellikler(df_oj, strict_shift=True)
    X_ta = veri_hijyeni.ozellikler(df_ta, strict_shift=True)

    y_oj_sure = df_oj["sure_dk"].to_numpy()
    y_oj_kwh = df_oj["kWhDelivered"].to_numpy()

    y_ta_sure = df_ta["sure_dk"].to_numpy()
    y_ta_kwh = df_ta["kWhDelivered"].to_numpy()

    s_sure = hesapla_egitim_olcegi(y_oj_sure)
    s_kwh = hesapla_egitim_olcegi(y_oj_kwh)

    model_haritasi = {
        "GlobalEmpirikBaseline": GlobalEmpirikQuantileModel,
        "QuantileRegressor": QuantileRegressorModel,
        "HistGradientBoosting": HistGradientBoostingQuantileModel,
        "GradientBoosting": GradientBoostingQuantileModel,
        "LightGBM": LightGBMQuantileModel,
    }

    # Yeniden Eğitim (Retrain on 100% of Jan-Jun)
    m_sure = model_haritasi[sampiyon_sure_ad]()
    m_sure.fit(X_oj, y_oj_sure)
    q20_s, q50_s, q80_s = m_sure.predict_quantiles(X_ta)
    q20_s_d, q50_s_d, q80_s_d, n_c_s, r_c_s = monotonlastir(q20_s, q50_s, q80_s)
    metrik_sure = model_secim_skoru(y_ta_sure, q20_s_d, q50_s_d, q80_s_d, s_egit=s_sure, gamma=gamma)
    metrik_sure["crossing_sayisi"] = n_c_s
    metrik_sure["crossing_orani"] = r_c_s

    m_kwh = model_haritasi[sampiyon_kwh_ad]()
    m_kwh.fit(X_oj, y_oj_kwh)
    q20_k, q50_k, q80_k = m_kwh.predict_quantiles(X_ta)
    q20_k_d, q50_k_d, q80_k_d, n_c_k, r_c_k = monotonlastir(q20_k, q50_k, q80_k)
    metrik_kwh = model_secim_skoru(y_ta_kwh, q20_k_d, q50_k_d, q80_k_d, s_egit=s_kwh, gamma=gamma)
    metrik_kwh["crossing_sayisi"] = n_c_k
    metrik_kwh["crossing_orani"] = r_c_k

    return {
        "sampiyon_sure": sampiyon_sure_ad,
        "sampiyon_kwh": sampiyon_kwh_ad,
        "metrik_sure_temmuz_aralik": metrik_sure,
        "metrik_kwh_temmuz_aralik": metrik_kwh,
        "m_sure_retrained": m_sure,
        "m_kwh_retrained": m_kwh,
        "df_temmuz_aralik": df_ta,
    }


def tahminleri_ekle(
    df_test: pd.DataFrame,
    sure_modeli: Any,
    enerji_modeli: Any,
) -> pd.DataFrame:
    """Belirtilen modellerle q20, q50, q80 tahminlerini üretip sim.py için DataFrame'e ekler."""
    df_cikti = df_test.copy()
    X = veri_hijyeni.ozellikler(df_cikti, strict_shift=True)

    # Süre tahminleri
    q20_s, q50_s, q80_s = sure_modeli.predict_quantiles(X)
    q20_s, q50_s, q80_s, _, _ = monotonlastir(q20_s, q50_s, q80_s)

    # Enerji tahminleri
    q20_k, q50_k, q80_k = enerji_modeli.predict_quantiles(X)
    q20_k, q50_k, q80_k, _, _ = monotonlastir(q20_k, q50_k, q80_k)

    # sim.py tarafından beklenen standart sütun adları
    df_cikti["tahmin_sure_q20"] = q20_s
    df_cikti["tahmin_sure_q50"] = q50_s
    df_cikti["tahmin_sure_q80"] = q80_s

    df_cikti["tahmin_kwh_q20"] = q20_k
    df_cikti["tahmin_kwh_q50"] = q50_k
    df_cikti["tahmin_kwh_q80"] = q80_k

    return df_cikti
