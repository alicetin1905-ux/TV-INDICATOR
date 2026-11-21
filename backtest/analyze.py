import pickle, sys, numpy as np
TF=sys.argv[1]; MINN=int(sys.argv[2]) if len(sys.argv)>2 else 12
from grid import EXITS
res=pickle.load(open(f"grid_{TF}.pkl","rb"))
rows=[]
for g,out in res:
    tr=[o[0] for o in out.values()]; te=[o[1] for o in out.values()]
    if min(s["n"] for s in tr)<MINN: continue
    rows.append((min(s["pf"] for s in tr), np.median([s["pf"] for s in tr]), g, out))
rows.sort(key=lambda r:(-r[0],-r[1]))
def fmt(g):
    (ef,es),adxm,vm,lf,uh,ex,lo=g
    return f"EMA{ef}/{es} adx>{adxm} vol>{vm} ema200={'J' if lf else 'N'} htf={'J' if uh else 'N'} exit={EXITS[ex]} {'LONG-only' if lo else 'long+short'}"
print(f"== {TF}: {len(rows)} configs met >= {MINN} trades/munt in train")
for mn,md,g,out in rows[:12]:
    print(f"\n{fmt(g)}\n  train minPF={mn:.2f} medPF={md:.2f}")
    for c,(a,b) in out.items():
        print(f"   {c:5} TRAIN n={a['n']:3} win={a['win']:4.1f}% pf={a['pf']:.2f} ret={a['ret']:7.1f}% dd={a['dd']:4.1f}%  |  TEST n={b['n']:3} win={b['win']:4.1f}% pf={b['pf']:.2f} ret={b['ret']:7.1f}% dd={b['dd']:4.1f}%")
# test-period robustness of top-50
top=rows[:50]
okt=[r for r in top if min(o[1]["pf"] for o in r[3].values())>1.0]
print(f"\nVan top-50 (train): {len(okt)} ook winstgevend (PF>1) op ALLE munten in test")
