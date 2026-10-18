"""Kapasite kısıtlı şarj simülatörü (15 dk adım, ayrık güç seviyeleri).

Her adımda planlayıcı yalnızca *inanılan* ayrılış adımı ve enerjiyi görür; araç gerçekte
bu bilgiye göre değil gerçek ayrılış adımında ayrılır ve gerçek enerjisi dolunca şarjı bırakır.
"""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

SEVIYELER = np.array([0, 8, 16, 24, 32]) * 0.208      # kW (208 V, ACN temel EVSE seviyeleri)
PMAX = float(SEVIYELER[-1])
DT_H = 0.25                                            # 15 dk
EPS = 1e-9


def _tavan_seviye(p):
    """p kW'ı karşılayan en küçük seviye."""
    k = SEVIYELER[SEVIYELER >= p - EPS]
    return float(k.min()) if k.size else PMAX


def _taban_seviye(p):
    """p kW'ı aşmayan en büyük seviye."""
    return float(SEVIYELER[SEVIYELER <= p + EPS].max())


def _sirali_dagit(sira, kalan, cap):
    hiz = np.zeros(len(kalan))
    rem = cap
    for i in sira:
        istek = _tavan_seviye(min(PMAX, max(kalan[i], 0.0) / DT_H))
        if istek <= 0:
            continue
        lv = _taban_seviye(min(rem, istek))
        hiz[i] = lv
        rem -= lv
    return hiz, rem


def _firsatci(hiz, rem, kalan, giris):
    """Artan kapasiteyi, inanılan enerjisi bitmiş ama hâlâ şarj çeken araçlara ver."""
    for i in np.argsort(giris, kind="stable"):
        if rem < SEVIYELER[1] - EPS:
            break
        if kalan[i] <= EPS and hiz[i] == 0:
            lv = _taban_seviye(min(rem, PMAX))
            hiz[i] = lv
            rem -= lv
    return hiz


def kural(ad):
    def f(t, kalan, dep, giris, cap):
        if ad == "fcfs":
            sira = np.argsort(giris, kind="stable")
        elif ad == "edf":
            sira = np.lexsort((giris, dep))
        elif ad == "llf":
            laxity = (dep - t) * DT_H - np.maximum(kalan, 0) / PMAX
            sira = np.lexsort((giris, laxity))
        else:
            raise ValueError(ad)
        hiz, rem = _sirali_dagit(sira, kalan, cap)
        return _firsatci(hiz, rem, kalan, giris)
    return f


def mpc(t, kalan, dep, giris, cap):
    m = len(kalan)
    L = np.maximum(dep - t, 1).astype(int)
    off = np.concatenate([[0], np.cumsum(L)])
    nvar = int(off[-1])
    H = int(L.max())
    s_idx = np.concatenate([np.arange(l) for l in L])
    w = 1.0 - 0.5 * s_idx / max(H, 1)
    c = -w * DT_H
    # kapasite satırları (adım başına) + enerji satırları (araç başına)
    rows, cols = [], []
    for i in range(m):
        rows.extend(np.arange(L[i]))
        cols.extend(off[i] + np.arange(L[i]))
    cap_A = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(H, nvar))
    er, ec = [], []
    for i in range(m):
        er.extend([i] * int(L[i]))
        ec.extend(off[i] + np.arange(L[i]))
    en_A = sparse.coo_matrix((np.full(len(er), DT_H), (er, ec)), shape=(m, nvar))
    A = sparse.vstack([cap_A, en_A]).tocsr()
    b = np.concatenate([np.full(H, cap), np.maximum(kalan, 0.0)])
    res = linprog(c, A_ub=A, b_ub=b, bounds=(0, PMAX), method="highs")
    if res.status != 0:
        return kural("edf")(t, kalan, dep, giris, cap)
    r0 = res.x[off[:-1]]
    hiz = np.array([_taban_seviye(x) for x in r0])
    rem = cap - hiz.sum()
    for i in np.argsort(-(r0 - hiz), kind="stable"):
        if r0[i] - hiz[i] <= 1e-6 or kalan[i] / DT_H <= hiz[i] + EPS:
            continue
        sonraki = SEVIYELER[SEVIYELER > hiz[i] + EPS]
        if sonraki.size and sonraki[0] - hiz[i] <= rem + EPS:
            rem -= sonraki[0] - hiz[i]
            hiz[i] = sonraki[0]
    return _firsatci(hiz, rem, kalan, giris)


def simule(giris, ayril, e_gercek, inan_ayril, inan_kwh, cap, yontem):
    """Dönen: araç başına teslim edilen kWh. Kapasite ihlali olursa hata verir."""
    n = len(giris)
    teslim = np.zeros(n)
    for t in range(int(ayril.max()) + 1):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e_gercek - EPS))[0]
        if aktif.size == 0:
            continue
        kalan = inan_kwh[aktif] - teslim[aktif]
        dep = np.maximum(inan_ayril[aktif], t + 1)
        hiz = yontem(t, kalan, dep, giris[aktif], cap)
        if hiz.sum() > cap + 1e-6:
            raise AssertionError(f"kapasite ihlali: {hiz.sum():.3f} > {cap:.3f}")
        teslim[aktif] += np.minimum(hiz * DT_H, e_gercek[aktif] - teslim[aktif])
    return teslim


def kontrolsuz_tepe(giris, ayril, e_gercek):
    """Kapasite sınırsız, herkes PMAX ile şarj: günün tepe gücü (kW)."""
    teslim = np.zeros(len(giris))
    tepe = 0.0
    for t in range(int(ayril.max()) + 1):
        aktif = np.where((giris <= t) & (t < ayril) & (teslim < e_gercek - EPS))[0]
        if aktif.size == 0:
            continue
        guc = np.minimum(PMAX, (e_gercek[aktif] - teslim[aktif]) / DT_H)
        teslim[aktif] += guc * DT_H
        tepe = max(tepe, guc.sum())
    return tepe


# ---- Tamamlama odaklı planlayıcı: hedefine ulaşan ARAÇ SAYISINI maksimize eden MILP ----
def mpc_milp(t, kalan, dep, giris, cap, hedef=0.95, sure_siniri=3.0):
    """Her araç için ikili 'tamamlandı' değişkeni z_i: sum(r_i)*dt >= hedef*kalan_i*z_i.
    Amaç: sum(z) maksimum, ikincil olarak toplam enerji. Çözülemezse enerji-LP'ye düşer."""
    from scipy.optimize import Bounds, LinearConstraint, milp
    m = len(kalan)
    L = np.maximum(dep - t, 1).astype(int)
    off = np.concatenate([[0], np.cumsum(L)])
    nr = int(off[-1])
    nvar = nr + m
    H = int(L.max())
    need = np.maximum(kalan, 0.0)
    s_idx = np.concatenate([np.arange(l) for l in L])
    w = 1.0 - 0.5 * s_idx / max(H, 1)
    scale = max(float(need.mean()), 1.0)
    c = np.zeros(nvar)
    c[:nr] = -0.02 * w * DT_H / scale        # ikincil: toplam enerji (erken tercih)
    c[nr:] = -1.0                              # birincil: tamamlanan araç sayısı
    rows, cols = [], []
    for i in range(m):
        rows.extend(np.arange(L[i]))
        cols.extend(off[i] + np.arange(L[i]))
    cap_A = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(H, nvar))
    er, ec = [], []
    for i in range(m):
        er.extend([i] * int(L[i]))
        ec.extend(off[i] + np.arange(L[i]))
    en = sparse.coo_matrix((np.full(len(er), DT_H), (er, ec)), shape=(m, nvar)).tocsr()
    zmat = sparse.coo_matrix((-(hedef * need), (np.arange(m), nr + np.arange(m))), shape=(m, nvar))
    cons = [LinearConstraint(cap_A.tocsr(), -np.inf, cap),
            LinearConstraint(en, -np.inf, need),
            LinearConstraint((en + zmat).tocsr(), 0.0, np.inf)]
    lb = np.zeros(nvar)
    ub = np.concatenate([np.full(nr, PMAX), np.ones(m)])
    integ = np.concatenate([np.zeros(nr), np.ones(m)])
    try:
        res = milp(c, constraints=cons, bounds=Bounds(lb, ub), integrality=integ,
                   options=dict(time_limit=sure_siniri, mip_rel_gap=0.01))
        ok = res.x is not None
    except Exception:
        ok = False
    if not ok:
        return mpc(t, kalan, dep, giris, cap)
    r0 = res.x[off[:-1]]
    hiz = np.array([_taban_seviye(x) for x in r0])
    rem = cap - hiz.sum()
    for i in np.argsort(-(r0 - hiz), kind="stable"):
        if r0[i] - hiz[i] <= 1e-6 or kalan[i] / DT_H <= hiz[i] + EPS:
            continue
        sonraki = SEVIYELER[SEVIYELER > hiz[i] + EPS]
        if sonraki.size and sonraki[0] - hiz[i] <= rem + EPS:
            rem -= sonraki[0] - hiz[i]
            hiz[i] = sonraki[0]
    return _firsatci(hiz, rem, kalan, giris)
