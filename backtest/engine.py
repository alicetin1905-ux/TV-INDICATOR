"""Python replica of TrendNavigator.pine logic for backtesting."""
import numpy as np
import pandas as pd

FEE = 0.0005      # 0.05% per side (taker)
SLIP = 0.0002     # 0.02% per side


def ema(x, n):
    x = np.asarray(x, float)
    out = np.full_like(x, np.nan)
    a = 2.0 / (n + 1)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    for i in range(n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def rma(x, n):
    x = np.asarray(x, float)
    out = np.full_like(x, np.nan)
    a = 1.0 / n
    # seed: SMA of first n non-nan values
    idx = np.where(~np.isnan(x))[0]
    if len(idx) < n:
        return out
    s = idx[0]
    out[s + n - 1] = np.nanmean(x[s:s + n])
    for i in range(s + n, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def indicators(df, p):
    h, l, c, v = df.h.values, df.l.values, df.c.values, df.v.values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    tr[0] = h[0] - l[0]
    up = h - np.r_[np.nan, h[:-1]]
    dn = np.r_[np.nan, l[:-1]] - l
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pdm[0] = mdm[0] = np.nan
    trur = rma(tr[1:], p["diLen"])
    trur = np.r_[np.nan, trur]
    dip = 100 * np.r_[np.nan, rma(pdm[1:], p["diLen"])] / trur
    dim = 100 * np.r_[np.nan, rma(mdm[1:], p["diLen"])] / trur
    s = dip + dim
    dx = np.abs(dip - dim) / np.where(s == 0, 1, s)
    adx = 100 * rma(dx, p["adxSmooth"])
    # RSI
    ch = np.diff(c, prepend=np.nan)
    g = rma(np.where(ch > 0, ch, 0.0)[1:], p["rsiLen"])
    ls = rma(np.where(ch < 0, -ch, 0.0)[1:], p["rsiLen"])
    rsi = np.r_[np.nan, 100 - 100 / (1 + g / np.where(ls == 0, 1e-12, ls))]
    atr = rma(tr, p["atrLen"])
    volavg = pd.Series(v).rolling(p["volLen"]).mean().values
    return dict(
        ef=ema(c, p["lenFast"]), es=ema(c, p["lenSlow"]),
        em=ema(c, p["lenMid"]), el=ema(c, p["lenLong"]),
        dip=dip, dim=dim, adx=adx, rsi=rsi, atr=atr,
        relvol=v / np.where(volavg > 0, volavg, np.nan),
    )


def htf_trend(df, rule, lenMid, lenLong):
    """Trend of the last *closed* HTF bar (= Pine [1] + lookahead_on)."""
    d = df.set_index("ts")
    hb = d.resample(rule, label="left", closed="left").agg({"c": "last"}).dropna()
    e1, e2 = ema(hb.c.values, lenMid), ema(hb.c.values, lenLong)
    c = hb.c.values
    t = np.where((c > e1) & (e1 > e2), 1, np.where((c < e1) & (e1 < e2), -1, 0))
    t = pd.Series(t, index=hb.index).shift(1).fillna(0)
    key = df.ts.dt.floor(rule)
    return key.map(t).fillna(0).values.astype(int)


def run(df, p, ind=None, htf=None, start=0, end=None, return_trades=False):
    ind = ind or indicators(df, p)
    n = len(df)
    end = n if end is None else end
    o, h, l, c = df.o.values, df.h.values, df.l.values, df.c.values
    ef, es, el = ind["ef"], ind["es"], ind["el"]
    dip, dim, adx, rsi, atr, rv = ind["dip"], ind["dim"], ind["adx"], ind["rsi"], ind["atr"], ind["relvol"]
    ht = htf if (htf is not None and p["useHtf"]) else np.zeros(n, int)

    bars_up = bars_dn = 10**9
    used_up = used_dn = True
    pos = 0; entry = sl = tp = ext = 0.0
    pending = 0  # signal waiting for next-open entry
    trades = []
    warm = max(p["lenLong"], 50) + 5
    for i in range(max(1, warm), end):
        # --- fill pending entry at this bar's open
        if pending != 0 and i >= start:
            if pos != 0:  # reverse: close at open
                trades.append(pos * (o[i] / entry - 1) - 2 * (FEE + SLIP))
            pos = pending; entry = o[i]
            sl = entry - pos * atr[i - 1] * p["slMult"]
            tp = entry + pos * atr[i - 1] * p["tpMult"] if p["tpMult"] > 0 else np.nan
            ext = entry
            pending = 0
        pending = 0
        # --- SL / TP intrabar
        if pos == 1:
            if l[i] <= sl:
                trades.append(sl / entry - 1 - 2 * (FEE + SLIP)); pos = 0
            elif not np.isnan(tp) and h[i] >= tp:
                trades.append(tp / entry - 1 - 2 * (FEE + SLIP)); pos = 0
        elif pos == -1:
            if h[i] >= sl:
                trades.append(1 - sl / entry - 2 * (FEE + SLIP)); pos = 0
            elif not np.isnan(tp) and l[i] <= tp:
                trades.append(1 - tp / entry - 2 * (FEE + SLIP)); pos = 0
        # --- trailing stop update (applies from next bar)
        tm = p.get("trailMult", 0)
        if tm > 0 and pos == 1:
            ext = max(ext, h[i]); sl = max(sl, ext - tm * atr[i])
        elif tm > 0 and pos == -1:
            ext = min(ext, l[i]); sl = min(sl, ext + tm * atr[i])
        # --- signals
        cu = ef[i] > es[i] and ef[i - 1] <= es[i - 1]
        cd = ef[i] < es[i] and ef[i - 1] >= es[i - 1]
        bars_up = 0 if cu else bars_up + 1
        bars_dn = 0 if cd else bars_dn + 1
        if cu: used_up = False
        if cd: used_dn = False
        adx_ok = adx[i] >= p["adxMin"] and (not p["useAdxUp"] or adx[i] > adx[i - 1])
        vol_ok = p["volMult"] <= 0 or (not np.isnan(rv[i]) and rv[i] >= p["volMult"])
        long_ok = adx_ok and vol_ok and dip[i] > dim[i] and (not p["useLongFilter"] or c[i] > el[i]) \
            and ht[i] >= 0 and (not p["useRsi"] or rsi[i] < p["rsiOB"])
        short_ok = adx_ok and vol_ok and dim[i] > dip[i] and (not p["useLongFilter"] or c[i] < el[i]) \
            and ht[i] <= 0 and (not p["useRsi"] or rsi[i] > p["rsiOS"])
        buy = bars_up <= p["sigWindow"] and ef[i] > es[i] and long_ok and not used_up
        sell = bars_dn <= p["sigWindow"] and ef[i] < es[i] and short_ok and not used_dn
        if buy: used_up = True
        if sell: used_dn = True
        if i < start:
            continue
        if buy and pos != 1:
            pending = 1
        elif sell:
            if p.get("longOnly"):
                if pos == 1:
                    trades.append(c[i] / entry - 1 - 2 * (FEE + SLIP)); pos = 0
            elif pos != -1:
                pending = -1
        # opposite cross exit (optional)
        if p.get("exitOnCross") and pos != 0 and pending == 0:
            if (pos == 1 and cd) or (pos == -1 and cu):
                trades.append(pos * (c[i] / entry - 1) - 2 * (FEE + SLIP)); pos = 0
    if pos != 0:
        trades.append(pos * (c[end - 1] / entry - 1) - 2 * (FEE + SLIP))
    if return_trades:
        return trades
    return stats(trades)


def stats(trades):
    t = np.array(trades)
    if len(t) == 0:
        return dict(n=0, win=0, pf=0, ret=0, dd=0, exp=0)
    eq = np.cumprod(1 + t)
    peak = np.maximum.accumulate(eq)
    gp, gl = t[t > 0].sum(), -t[t < 0].sum()
    return dict(n=len(t), win=(t > 0).mean() * 100, pf=gp / gl if gl > 0 else 99,
                ret=(eq[-1] - 1) * 100, dd=((peak - eq) / peak).max() * 100, exp=t.mean() * 100)


DEFAULT = dict(lenFast=9, lenSlow=21, lenMid=50, lenLong=200, diLen=14, adxSmooth=14,
               adxMin=20, adxStrong=30, useAdxUp=False, volLen=20, volMult=1.2,
               sigWindow=3, useLongFilter=True, useRsi=True, rsiLen=14, rsiOB=70, rsiOS=30,
               useHtf=True, atrLen=14, slMult=1.5, tpMult=3.0, longOnly=False, exitOnCross=False)


def load(coin, tf):
    df = pd.read_csv(f"data/{coin}_{tf}.csv", parse_dates=["ts"])
    return df.reset_index(drop=True)
