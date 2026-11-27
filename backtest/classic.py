"""Klassieke TradingView-strategieën naast Trend Navigator.

Elke strategie volgt de ingebouwde TradingView-versie (zelfde indicator-formules
als ta.*). Signaal op de close, uitvoering op de open van de volgende candle,
0,07% kosten per kant, 100% van het kapitaal per trade, geen hefboom.
Train = eerste 65% van de data, test = laatste 35% (zelfde split als grid.py).

    python3 classic.py          # tabel + results_classic.md

ClassicStrategies.pine bevat dezelfde regels voor de Strategy Tester.
"""
import numpy as np
import pandas as pd
from engine import ema, rma, load, FEE, SLIP
from engine2 import run2, stats2, btc_trend, htf_trend, indicators, BASE

COST = 2 * (FEE + SLIP)
COINS = ["BTC", "ETH", "SOL", "HYPE"]
SPLIT = 0.65


# ─── indicatoren (Pine-equivalent) ──────────────────────────────────────────────
def sma(x, n):
    return pd.Series(x).rolling(n).mean().values


def wma(x, n):
    w = np.arange(1, n + 1, dtype=float)
    return pd.Series(x).rolling(n).apply(lambda a: (a * w).sum() / w.sum(), raw=True).values


def hma(x, n):
    return wma(2 * wma(x, n // 2) - wma(x, n), int(np.floor(np.sqrt(n))))


def highest(x, n):
    return pd.Series(x).rolling(n).max().values


def lowest(x, n):
    return pd.Series(x).rolling(n).min().values


def prev(x, k=1):
    return np.r_[np.full(k, np.nan), x[:-k]]


def true_range(h, l, c):
    pc = prev(c)
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    tr[0] = h[0] - l[0]
    return tr


def rsi(c, n=14):
    ch = np.diff(c, prepend=np.nan)
    g = rma(np.where(ch > 0, ch, 0.0)[1:], n)
    ls = rma(np.where(ch < 0, -ch, 0.0)[1:], n)
    return np.r_[np.nan, 100 - 100 / (1 + g / np.where(ls == 0, 1e-12, ls))]


def dmi(h, l, c, n=14, sm=14):
    tr = true_range(h, l, c)
    up, dn = h - prev(h), prev(l) - l
    pdm = np.where((up > dn) & (up > 0), up, 0.0)[1:]
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)[1:]
    trr = rma(tr[1:], n)
    dip = np.r_[np.nan, 100 * rma(pdm, n) / trr]
    dim = np.r_[np.nan, 100 * rma(mdm, n) / trr]
    s = dip + dim
    adx = 100 * rma(np.abs(dip - dim) / np.where(s == 0, 1, s), sm)
    return dip, dim, adx


def supertrend(h, l, c, factor=3.0, n=10):
    """ta.supertrend: dir 1 = uptrend (Pine geeft -1 voor up)."""
    atr = rma(true_range(h, l, c), n)
    hl2 = (h + l) / 2
    ub, lb = hl2 + factor * atr, hl2 - factor * atr
    d = np.zeros(len(c), int); st = np.full(len(c), np.nan)
    fu, fl = ub.copy(), lb.copy()
    for i in range(1, len(c)):
        if np.isnan(atr[i - 1]):
            d[i] = 1; continue
        fl[i] = lb[i] if (lb[i] > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
        fu[i] = ub[i] if (ub[i] < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
        if np.isnan(st[i - 1]):
            d[i] = -1
        elif st[i - 1] == fu[i - 1]:
            d[i] = 1 if c[i] > fu[i] else -1
        else:
            d[i] = -1 if c[i] < fl[i] else 1
        st[i] = fl[i] if d[i] == 1 else fu[i]
    return d


def psar(h, l, start=0.02, inc=0.02, mx=0.2):
    n = len(h); sar = np.full(n, np.nan)
    up = h[1] >= h[0]
    ep = h[1] if up else l[1]; s = l[0] if up else h[0]; af = start
    sar[1] = s
    for i in range(2, n):
        s = s + af * (ep - s)
        if up:
            s = min(s, l[i - 1], l[i - 2])
            if l[i] < s:
                up, s, ep, af = False, ep, l[i], start
            elif h[i] > ep:
                ep = h[i]; af = min(af + inc, mx)
        else:
            s = max(s, h[i - 1], h[i - 2])
            if h[i] > s:
                up, s, ep, af = True, ep, h[i], start
            elif l[i] < ep:
                ep = l[i]; af = min(af + inc, mx)
        sar[i] = s
    return sar


def cross_over(a, b):
    return (a > b) & (prev(a) <= prev(b))


def cross_under(a, b):
    return (a < b) & (prev(a) >= prev(b))


# ─── strategieën: (long_entry, short_entry, long_exit, short_exit) ──────────────
def s_ema_cross(d):
    c = d.c.values
    a, b = ema(c, 9), ema(c, 21)
    return a > b, a < b, None, None


def s_golden_cross(d):
    c = d.c.values
    a, b = sma(c, 50), sma(c, 200)
    return a > b, a < b, None, None


def s_macd(d):
    c = d.c.values
    m = ema(c, 12) - ema(c, 26)
    sig = ema(m[~np.isnan(m)], 9)
    sig = np.r_[np.full(np.isnan(m).sum(), np.nan), sig]
    return cross_over(m, sig), cross_under(m, sig), None, None


def s_supertrend(d):
    dr = supertrend(d.h.values, d.l.values, d.c.values)
    return dr == 1, dr == -1, None, None


def s_rsi(d):
    r = rsi(d.c.values, 14)
    return cross_over(r, np.full_like(r, 30)), cross_under(r, np.full_like(r, 70)), None, None


def s_bollinger(d):
    c = d.c.values
    basis = sma(c, 20); dev = 2 * pd.Series(c).rolling(20).std(ddof=0).values
    return cross_over(c, basis - dev), cross_under(c, basis + dev), None, None


def s_donchian(d):
    h, l, c = d.h.values, d.l.values, d.c.values
    return (c > prev(highest(h, 20)), c < prev(lowest(l, 20)),
            c < prev(lowest(l, 10)), c > prev(highest(h, 10)))


def s_ichimoku(d):
    h, l, c = d.h.values, d.l.values, d.c.values
    ten = (highest(h, 9) + lowest(l, 9)) / 2
    kij = (highest(h, 26) + lowest(l, 26)) / 2
    sa = prev((ten + kij) / 2, 25)
    sb = prev((highest(h, 52) + lowest(l, 52)) / 2, 25)
    top, bot = np.fmax(sa, sb), np.fmin(sa, sb)
    lc = (ten > kij) & (c > top)
    sc = (ten < kij) & (c < bot)
    return lc, sc, ~lc, ~sc


def s_psar(d):
    c = d.c.values
    s = psar(d.h.values, d.l.values)
    return c > s, c < s, None, None


def s_keltner(d):
    h, l, c = d.h.values, d.l.values, d.c.values
    m = ema(c, 20); rng = ema(true_range(h, l, c), 20)
    return cross_over(c, m + 2 * rng), cross_under(c, m - 2 * rng), None, None


def s_stoch(d):
    h, l, c = d.h.values, d.l.values, d.c.values
    raw = 100 * (c - lowest(l, 14)) / (highest(h, 14) - lowest(l, 14))
    k = sma(raw, 3); dd = sma(k, 3)
    return cross_over(k, dd) & (k < 20), cross_under(k, dd) & (k > 80), None, None


def s_hma(d):
    x = hma(d.c.values, 55)
    return (x > prev(x)), (x < prev(x)), None, None


def s_dmi(d):
    dip, dim, adx = dmi(d.h.values, d.l.values, d.c.values)
    lc = (dip > dim) & (adx > 20)
    sc = (dim > dip) & (adx > 20)
    return lc, sc, ~lc, ~sc


def s_momentum(d):
    c = d.c.values
    m0 = c - prev(c, 12); m1 = m0 - prev(m0)
    return (m0 > 0) & (m1 > 0), (m0 < 0) & (m1 < 0), None, None


STRATS = {
    "EMA 9/21 cross": s_ema_cross,
    "Golden cross SMA 50/200": s_golden_cross,
    "MACD 12/26/9": s_macd,
    "Supertrend 10/3": s_supertrend,
    "RSI 30/70 reversal": s_rsi,
    "Bollinger 20/2 reversal": s_bollinger,
    "Donchian/Turtle 20/10": s_donchian,
    "Ichimoku 9/26/52": s_ichimoku,
    "Parabolic SAR": s_psar,
    "Keltner 20/2 breakout": s_keltner,
    "Stochastic 14/3/3": s_stoch,
    "Hull MA 55 slope": s_hma,
    "DMI/ADX>20": s_dmi,
    "Momentum 12": s_momentum,
}


# ─── simulatie ──────────────────────────────────────────────────────────────────
def simulate(d, sig, long_only=False):
    """Geeft lijst van (rendement, entry_index)."""
    le, se, lx, sx = (None if a is None else np.nan_to_num(a).astype(bool) for a in sig)
    o, c = d.o.values, d.c.values
    n = len(c); pos = 0; entry = 0.0; ei = 0; trades = []
    target = None
    for i in range(1, n):
        if target is not None and target != pos:  # uitvoeren op de open
            if pos != 0:
                trades.append((pos * (o[i] / entry - 1) - COST, ei))
            pos = target
            if pos != 0:
                entry, ei = o[i], i
        target = None
        if le[i] and pos != 1:
            target = 1
        elif se[i] and pos != -1:
            target = 0 if long_only else -1
            if long_only and pos == 0:
                target = None
        elif pos == 1 and lx is not None and lx[i]:
            target = 0
        elif pos == -1 and sx is not None and sx[i]:
            target = 0
    if pos != 0:
        trades.append((pos * (c[-1] / entry - 1) - COST, ei))
    return trades


def stats(rets):
    if len(rets) == 0:
        return dict(n=0, win=0.0, pf=0.0, ret=0.0, dd=0.0)
    r = np.maximum(np.asarray(rets), -1.0)  # meer dan 100% verlies kan niet: account is leeg
    eq = np.cumprod(1 + r); peak = np.maximum.accumulate(np.r_[1, eq])[1:]
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    return dict(n=len(r), win=(r > 0).mean() * 100, pf=gp / gl if gl > 0 else 99.0,
                ret=(eq[-1] - 1) * 100, dd=((peak - eq) / peak).max() * 100)


def evaluate(d, sig, long_only):
    t = simulate(d, sig, long_only)
    cut = int(len(d) * SPLIT)
    return (stats([r for r, _ in t]), stats([r for r, i in t if i < cut]),
            stats([r for r, i in t if i >= cut]))


def trend_navigator(D):
    p = dict(BASE, useBtc=True, reEntry=True, reStrictHtf=True, reNeedRibbon=False,
             reNeedAdx=False, reMax=1)
    out = {}
    for coin, d in D.items():
        ind, ht = indicators(d, p), htf_trend(d, "1D", 50, 200)
        bt = btc_trend(D["BTC"], d.ts.values, None)
        n = len(d); cut = int(n * SPLIT)
        f = stats2(run2(d, p, ind, ht, bt))
        tr = stats2(run2(d, p, ind, ht, bt, 0, cut))
        te = stats2(run2(d, p, ind, ht, bt, cut, n))
        out[coin] = (f, tr, te)
    return out


def main():
    D = {c: load(c, "4H") for c in COINS}
    rows = []
    for name, fn in STRATS.items():
        for lo in (False, True):
            res = {}
            for coin, d in D.items():
                res[coin] = evaluate(d, fn(d), lo)
            rows.append((name, "long" if lo else "L+S", res))
    rows.append(("Trend Navigator (repo)", "L+S", trend_navigator(D)))
    bh = {}
    for coin, d in D.items():
        cut = int(len(d) * SPLIT)
        bh[coin] = ((d.c.iloc[-1] / d.o.iloc[0] - 1) * 100,
                    (d.c.iloc[cut - 1] / d.o.iloc[0] - 1) * 100,
                    (d.c.iloc[-1] / d.o.iloc[cut] - 1) * 100)

    main3 = ["BTC", "ETH", "SOL"]

    def score(res):  # slechtste munt (BTC/ETH/SOL), test-PF eerst
        return (min(res[c][2]["pf"] for c in main3), min(res[c][0]["pf"] for c in main3))

    rows.sort(key=lambda r: score(r[2]), reverse=True)

    L = []
    L.append("# Klassieke strategieën vs Trend Navigator (4H, OKX spot)\n")
    L.append(f"Data: {D['BTC'].ts.min():%d-%m-%Y} – {D['BTC'].ts.max():%d-%m-%Y} "
             f"(HYPE vanaf {D['HYPE'].ts.min():%d-%m-%Y}). Kosten 0,07%/kant, 100% kapitaal, "
             "geen hefboom. Test = laatste 35%. Gesorteerd op de slechtste test-PF van BTC/ETH/SOL.\n")
    L.append("PF = profit factor. **vet** = test-PF > 1 op BTC, ETH én SOL.\n")
    L.append("| # | Strategie | Modus | Min test-PF (B/E/S) | " +
             " | ".join(f"{c} PF train→test · rend. · DD" for c in COINS) + " |")
    L.append("|---|---|---|---|" + "---|" * len(COINS))
    for k, (name, mode, res) in enumerate(rows, 1):
        mt = score(res)[0]
        cells = []
        for c in COINS:
            f, tr, te = res[c]
            cells.append(f"{tr['pf']:.2f}→{te['pf']:.2f} · {f['ret']:+.0f}% · {f['dd']:.0f}% ({f['n']})")
        nm = f"**{name}**" if mt > 1 else name
        L.append(f"| {k} | {nm} | {mode} | {mt:.2f} | " + " | ".join(cells) + " |")
    L.append("| | Buy & hold | | | " + " | ".join(
        f"train {bh[c][1]:+.0f}% · test {bh[c][2]:+.0f}% · tot. {bh[c][0]:+.0f}%" for c in COINS) + " |")
    L.append("\nCel: PF train→test · totaalrendement · max drawdown (gesloten trades) (aantal trades).")
    txt = "\n".join(L)
    open("results_classic.md", "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
