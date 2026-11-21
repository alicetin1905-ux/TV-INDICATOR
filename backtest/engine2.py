"""Engine v2: v1-logica + herinstap, wijdere trail in sterke trend, BTC-filter,
en positiegrootte op basis van risico. Zelfde conventies als engine.py."""
import numpy as np
import pandas as pd
from engine import ema, indicators, htf_trend, load, DEFAULT, FEE, SLIP

COST = 2 * (FEE + SLIP)


def btc_trend(btc_df, target_ts, rule=None, lenMid=50, lenLong=200):
    """BTC-trend (1/0/-1) uitgelijnd op target_ts.
    rule=None: zelfde timeframe (close > EMA50 > EMA200); rule='1D': dagtrend (bevestigd)."""
    if rule is None:
        c = btc_df.c.values
        e1, e2 = ema(c, lenMid), ema(c, lenLong)
        t = np.where((c > e1) & (e1 > e2), 1, np.where((c < e1) & (e1 < e2), -1, 0))
        s = pd.Series(t, index=btc_df.ts)
    else:
        s = pd.Series(htf_trend(btc_df, rule, lenMid, lenLong), index=btc_df.ts)
    return pd.Series(target_ts).map(s).fillna(0).values.astype(int)


def run2(df, p, ind=None, htf=None, btc=None, start=0, end=None):
    """Geeft lijst van (rendement, stopafstand_fractie, type) per trade."""
    ind = ind or indicators(df, p)
    n = len(df)
    end = n if end is None else end
    o, h, l, c = df.o.values, df.h.values, df.l.values, df.c.values
    ef, es, em, el = ind["ef"], ind["es"], ind["em"], ind["el"]
    dip, dim, adx, rsi, atr, rv = ind["dip"], ind["dim"], ind["adx"], ind["rsi"], ind["atr"], ind["relvol"]
    ht = htf if (htf is not None and p["useHtf"]) else np.zeros(n, int)
    bt = btc if (btc is not None and p.get("useBtc")) else np.zeros(n, int)

    bars_up = bars_dn = 10**9
    used_up = used_dn = True
    pos = 0; entry = sl = tp = ext = sdist = 0.0; kind = ""
    pending = 0; pend_kind = ""
    can_re = 0; re_count = 0
    trades = []
    warm = max(p["lenLong"], 50) + 5

    def close_trade(px):
        trades.append((pos * (px / entry - 1) - COST, sdist, kind))

    for i in range(warm, end):
        # --- fill pending entry at open
        if pending != 0 and i >= start:
            if pos != 0:
                close_trade(o[i])
            pos = pending; entry = o[i]; kind = pend_kind
            sl = entry - pos * atr[i - 1] * p["slMult"]
            sdist = abs(entry - sl) / entry
            tp = entry + pos * atr[i - 1] * p["tpMult"] if p["tpMult"] > 0 else np.nan
            ext = entry
        pending = 0
        # --- stop / tp
        stopped = 0
        if pos == 1:
            if l[i] <= sl:
                close_trade(sl); stopped = 1; pos = 0
            elif not np.isnan(tp) and h[i] >= tp:
                close_trade(tp); pos = 0
        elif pos == -1:
            if h[i] >= sl:
                close_trade(sl); stopped = -1; pos = 0
            elif not np.isnan(tp) and l[i] <= tp:
                close_trade(tp); pos = 0
        if stopped:
            can_re = stopped
        # --- trailing (wijder in sterke trend)
        tm = p.get("trailMult", 0)
        tb = p.get("trailBull", 0)
        if tm > 0 and pos == 1:
            m = tb if (tb > 0 and ht[i] == 1) else tm
            ext = max(ext, h[i]); sl = max(sl, ext - m * atr[i])
        elif tm > 0 and pos == -1:
            m = tb if (tb > 0 and ht[i] == -1) else tm
            ext = min(ext, l[i]); sl = min(sl, ext + m * atr[i])
        # --- signalen
        cu = ef[i] > es[i] and ef[i - 1] <= es[i - 1]
        cd = ef[i] < es[i] and ef[i - 1] >= es[i - 1]
        bars_up = 0 if cu else bars_up + 1
        bars_dn = 0 if cd else bars_dn + 1
        if cu: used_up = False
        if cd: used_dn = False
        adx_ok = adx[i] >= p["adxMin"] and (not p["useAdxUp"] or adx[i] > adx[i - 1])
        vol_ok = p["volMult"] <= 0 or (not np.isnan(rv[i]) and rv[i] >= p["volMult"])
        long_ok = adx_ok and vol_ok and dip[i] > dim[i] and (not p["useLongFilter"] or c[i] > el[i]) \
            and ht[i] >= 0 and bt[i] >= 0 and (not p["useRsi"] or rsi[i] < p["rsiOB"])
        short_ok = adx_ok and vol_ok and dim[i] > dip[i] and (not p["useLongFilter"] or c[i] < el[i]) \
            and ht[i] <= 0 and bt[i] <= 0 and (not p["useRsi"] or rsi[i] > p["rsiOS"])
        buy = bars_up <= p["sigWindow"] and ef[i] > es[i] and long_ok and not used_up
        sell = bars_dn <= p["sigWindow"] and ef[i] < es[i] and short_ok and not used_dn
        if buy: used_up = True
        if sell: used_dn = True
        if buy or sell:
            can_re = 0; re_count = 0

        # --- herinstap na stop, trend intact
        re_buy = re_sell = False
        if p.get("reEntry") and pos == 0 and can_re != 0 and re_count < p.get("reMax", 99):
            need_ht = 1 if p.get("reStrictHtf") else 0
            if can_re == 1:
                ok = (c[i] > ef[i] and c[i - 1] <= ef[i - 1] and em[i] > el[i] and c[i] > el[i]
                      and ht[i] >= need_ht and bt[i] >= 0 and dip[i] > dim[i]
                      and (not p.get("reNeedRibbon") or ef[i] > es[i])
                      and (not p.get("reNeedAdx") or adx[i] >= p["adxMin"])
                      and (not p["useRsi"] or rsi[i] < p["rsiOB"]))
                re_buy = ok
            else:
                ok = (c[i] < ef[i] and c[i - 1] >= ef[i - 1] and em[i] < el[i] and c[i] < el[i]
                      and ht[i] <= -need_ht and bt[i] <= 0 and dim[i] > dip[i]
                      and (not p.get("reNeedRibbon") or ef[i] < es[i])
                      and (not p.get("reNeedAdx") or adx[i] >= p["adxMin"])
                      and (not p["useRsi"] or rsi[i] > p["rsiOS"]))
                re_sell = ok
            # trend gebroken → herinstap vervalt
            if can_re == 1 and em[i] < el[i]: can_re = 0
            if can_re == -1 and em[i] > el[i]: can_re = 0

        if i < start:
            continue
        if buy and pos != 1:
            pending = 1; pend_kind = "sig"
        elif sell:
            if p.get("longOnly"):
                if pos == 1:
                    close_trade(c[i]); pos = 0
            elif pos != -1:
                pending = -1; pend_kind = "sig"
        elif re_buy:
            pending = 1; pend_kind = "re"; re_count += 1
        elif re_sell and not p.get("longOnly"):
            pending = -1; pend_kind = "re"; re_count += 1
    if pos != 0:
        close_trade(c[end - 1])
    return trades


def stats2(trades, riskPct=None, maxLev=1.0):
    """riskPct=None: 100% kapitaal per trade. Anders: grootte = risk / stopafstand (max maxLev)."""
    if not trades:
        return dict(n=0, win=0, pf=0, ret=0, dd=0, re=0)
    r = np.array([t[0] for t in trades]); sd = np.array([t[1] for t in trades])
    size = np.ones_like(r) if riskPct is None else np.minimum(riskPct / 100 / np.maximum(sd, 1e-6), maxLev)
    rr = r * size
    eq = np.cumprod(1 + rr); peak = np.maximum.accumulate(np.r_[1, eq])[1:]
    gp, gl = rr[rr > 0].sum(), -rr[rr < 0].sum()
    return dict(n=len(r), win=(r > 0).mean() * 100, pf=gp / gl if gl > 0 else 99,
                ret=(eq[-1] - 1) * 100, dd=((peak - eq) / peak).max() * 100,
                re=sum(1 for t in trades if t[2] == "re"), avgsize=size.mean())


BASE = dict(DEFAULT, lenFast=9, lenSlow=21, adxMin=15, volMult=1.0, useLongFilter=True, useHtf=True,
            slMult=2, tpMult=0, trailMult=3)
