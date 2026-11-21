import numpy as np, pandas as pd
from engine import load, ema
rows=[]
for coin in ["BTC","ETH","SOL","HYPE"]:
    px=load(coin,"4H"); px["e200"]=ema(px.c.values,200); px["e50"]=ema(px.c.values,50)
    oi=pd.read_csv(f"data/{coin}_OI_4H.csv",parse_dates=["ts"])
    df=px.merge(oi,on="ts").reset_index(drop=True)
    df["doi"]=df.oiUsd.pct_change(); df["z"]=df.doi/df.doi.rolling(50,min_periods=20).std()
    for h in [1,3,6,12]: df[f"f{h}"]=df.c.shift(-h)/df.c-1
    df["coin"]=coin; rows.append(df.dropna())
d=pd.concat(rows)
up=(d.c>d.e200); 
for z in [2.0,2.5]:
    L=(d.z<=-z)&(d.c<d.o); S=(d.z<=-z)&(d.c>d.o)
    print(f"\n== z<=-{z}   (forward rendement gemiddeld, %; hit = % positief)")
    for name,m in [("alle bars (basis)",d.z.notna()),("LONG-liq (rode candle)",L),("  ..in uptrend (>EMA200)",L&up),("  ..in downtrend",L&~up),("SHORT-liq (groene candle)",S),("  ..in uptrend",S&up),("  ..in downtrend",S&~up)]:
        x=d[m]; print(f"{name:28} n={len(x):4}  "+"  ".join(f"+{h*4}h: {x[f'f{h}'].mean()*100:+.2f}% ({(x[f'f{h}']>0).mean()*100:.0f}%)" for h in [1,3,6,12]))
