import numpy as np, pandas as pd
allr=pd.read_pickle("liq5m.pkl")
for zthr in [1.5,2.0,2.5]:
    tot=dict(ev=0,hit=0,dir=0,cap=0,capd=0)
    for coin,k,oi,L in allr:
        df=k.set_index("ts").join(oi.set_index("ts").oi).join(L).fillna({"long":0,"short":0}).dropna()
        df["doi"]=df.oi.pct_change()
        sd=df.doi.rolling(50,min_periods=20).std()
        df["z"]=df.doi/sd
        df["liq"]=df.long+df.short
        df=df[df.index>=L.index.min()].dropna()
        big=df.liq>=df.liq.quantile(0.9)
        ev=(df.z<=-zthr)&(df.c!=df.o)
        evlong=ev&(df.c<df.o)  # predicted long liqs
        tot["ev"]+=ev.sum(); tot["hit"]+=(ev&big).sum()
        tot["dir"]+=((evlong&(df.long>df.short))|(ev&~evlong&(df.short>df.long))).sum()
        tot["cap"]+=df.liq[ev].sum(); tot["capd"]+=df.liq.sum()
    print(f"z<=-{zthr}: events={tot['ev']}  in top-10% liq-bars={tot['hit']/tot['ev']*100:.0f}% (toeval 10%)  richting juist={tot['dir']/tot['ev']*100:.0f}%  vangt {tot['cap']/tot['capd']*100:.0f}% van alle liq-volume")
