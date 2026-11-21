import itertools, numpy as np, pandas as pd
from engine import *
COINS=["BTC","ETH","SOL","HYPE"]
D={c:load(c,"4H") for c in COINS}
BASE=dict(DEFAULT,lenFast=9,lenSlow=21,adxMin=15,volMult=1.0,useLongFilter=True,useHtf=False,slMult=2,tpMult=0,trailMult=3)
HT={c:htf_trend(D[c],"1D",50,200) for c in COINS}
def allc(p):
    return {c:run(D[c],p,htf=HT[c]) for c in COINS}
def line(tag,r):
    pf=[r[c]["pf"] for c in COINS]
    print(f"{tag:38} "+"  ".join(f"{c}:pf={r[c]['pf']:.2f} ret={r[c]['ret']:6.0f}% dd={r[c]['dd']:3.0f}% n={r[c]['n']}" for c in COINS)+f"  | minPF={min(pf):.2f}")
line("BASIS (volledige periode)",allc(BASE))
print("\n-- gevoeligheid (1 parameter tegelijk) --")
for k,vals in [("adxMin",[10,12,18,20,25]),("volMult",[0,0.8,1.2,1.5]),("slMult",[1.5,2.5,3]),("trailMult",[2,2.5,3.5,4,5]),
               ("lenFast",[8,10,12]),("lenSlow",[18,26,30]),("sigWindow",[0,1,5]),("useRsi",[False]),("useHtf",[True]),("useLongFilter",[False]),("longOnly",[True])]:
    for v in vals:
        line(f"{k}={v}",allc(dict(BASE,**{k:v})))
print("\n-- per jaar (BASIS) vs buy&hold --")
for c in COINS:
    df=D[c]; ind=indicators(df,BASE)
    for y in sorted(df.ts.dt.year.unique()):
        idx=np.where(df.ts.dt.year==y)[0]
        s=run(df,BASE,ind,HT[c],idx[0],idx[-1]+1)
        bh=(df.c.iloc[idx[-1]]/df.c.iloc[idx[0]]-1)*100
        print(f"{c:5} {y}  n={s['n']:3} win={s['win']:4.1f}% pf={s['pf']:.2f} ret={s['ret']:7.1f}% dd={s['dd']:4.1f}%   B&H={bh:7.1f}%")
