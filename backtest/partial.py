import itertools, numpy as np
from engine2 import *
COINS=["BTC","ETH","SOL","HYPE"]
D={c:load(c,"4H") for c in COINS}
RE=dict(reEntry=True,reStrictHtf=True,reNeedRibbon=False,reNeedAdx=False,reMax=1)
P=dict(BASE,useBtc=True,**RE)
PRE={}
for c in COINS:
    df=D[c]; PRE[c]=(indicators(df,P),htf_trend(df,"1D",50,200),btc_trend(D["BTC"],df.ts.values,None))
VAR=[("HUIDIG (geen deel-TP)",dict())]+[(f"{f:.0%} op {r}R{' + BE' if be else ''}",dict(ptR=r,ptFrac=f,ptBE=be))
     for r,f,be in itertools.product([1,1.5,2,3],[0.33,0.5],[True,False])]
rows=[]
for name,v in VAR:
    p=dict(P,**v); tr=[];te=[];fu=[]
    for c in COINS:
        df=D[c]; ind,ht,bt=PRE[c]; n=len(df); cut=int(n*.65)
        tr.append(stats2(run2(df,p,ind,ht,bt,0,cut))); te.append(stats2(run2(df,p,ind,ht,bt,cut,n)))
        fu.append(stats2(run2(df,p,ind,ht,bt),2,3))
    rows.append((name,tr,te,fu))
print(f"{'variant':24} {'trainMinPF':>10} {'testMinPF':>9} | "+" | ".join(f"{c}: win  PF   ret/dd (2%)" for c in COINS))
for name,tr,te,fu in rows:
    print(f"{name:24} {min(x['pf'] for x in tr):10.2f} {min(x['pf'] for x in te):9.2f} | "+" | ".join(f"{c} {f['win']:3.0f}% {f['pf']:.2f} {f['ret']:+4.0f}/{f['dd']:2.0f}%" for c,f in zip(COINS,fu)))
