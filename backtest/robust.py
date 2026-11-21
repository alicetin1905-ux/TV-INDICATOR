import pickle,sys,collections
from grid import EXITS
TF=sys.argv[1]; MINN=int(sys.argv[2])
res=pickle.load(open(f"grid_{TF}.pkl","rb"))
rows=[]
for g,out in res:
    tr=[o[0] for o in out.values()]
    if min(s["n"] for s in tr)<MINN: continue
    rows.append((min(s["pf"] for s in tr),g,out))
rows.sort(key=lambda r:-r[0])
for mn,g,out in rows[:50]:
    if min(o[1]["pf"] for o in out.values())<=1: continue
    (ef,es),a,v,lf,uh,ex,lo=g
    print(f"EMA{ef}/{es} adx>{a} vol>{v} ema200={lf} htf={uh} {EXITS[ex]} {'LONG' if lo else 'L+S'}")
    for c,(x,y) in out.items():
        print(f"   {c:5} TRAIN n={x['n']:3} pf={x['pf']:.2f} ret={x['ret']:6.1f}% dd={x['dd']:4.1f}% | TEST n={y['n']:3} pf={y['pf']:.2f} ret={y['ret']:6.1f}% dd={y['dd']:4.1f}%")
print()
top=rows[:200]
for k,name in [(0,"EMA"),(1,"ADX"),(2,"VOL"),(3,"EMA200"),(4,"HTF"),(5,"EXIT"),(6,"LONGONLY")]:
    print(name,dict(collections.Counter(r[1][k] for r in top)))
