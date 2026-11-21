import numpy as np
from engine2 import *
COINS=["BTC","ETH","SOL","HYPE"]
D={c:load(c,"4H") for c in COINS}
RE=dict(reEntry=True,reStrictHtf=True,reNeedRibbon=False,reNeedAdx=False,reMax=1)
CFG={"OUD":dict(BASE),"HERINSTAP":dict(BASE,**RE),"HERINSTAP+BTC":dict(BASE,useBtc=True,**RE)}
PRE={c:(indicators(D[c],BASE),htf_trend(D[c],"1D",50,200),btc_trend(D["BTC"],D[c].ts.values,None)) for c in COINS}
print("== per jaar: rendement (100% kapitaal)  vs buy&hold")
for c in COINS:
    df=D[c]; ind,ht,bt=PRE[c]
    for y in sorted(df.ts.dt.year.unique()):
        idx=np.where(df.ts.dt.year==y)[0]
        if len(idx)<300: continue
        bh=(df.c.iloc[idx[-1]]/df.c.iloc[idx[0]]-1)*100
        cells=[]
        for k,p in CFG.items():
            s=stats2(run2(df,p,ind,ht,bt,idx[0],idx[-1]+1)); cells.append(f"{k}: {s['ret']:+6.0f}%")
        print(f"{c:5} {y}  "+"  ".join(cells)+f"   | B&H {bh:+6.0f}%")
print("\n== positiegrootte (HERINSTAP+BTC, volledige periode)")
for c in COINS:
    df=D[c]; ind,ht,bt=PRE[c]; t=run2(df,CFG["HERINSTAP+BTC"],ind,ht,bt)
    out=[]
    for lab,rk,ml in [("100% kapitaal",None,1),("1% risico max1x",1,1),("1% risico max3x",1,3),("2% risico max3x",2,3)]:
        s=stats2(t,rk,ml); out.append(f"{lab}: ret {s['ret']:+5.0f}% dd {s['dd']:4.1f}% gem.grootte {s.get('avgsize',1):.2f}x")
    sd=np.median([x[1] for x in t])*100
    print(f"{c:5} (mediaan stopafstand {sd:.1f}%)\n   "+"\n   ".join(out))
