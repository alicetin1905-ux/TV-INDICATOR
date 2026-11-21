import itertools, pickle, sys
from multiprocessing import Pool
import numpy as np
from engine import *
HTF={"15m":"1h","1H":"4h","4H":"1D"}
TF=sys.argv[1]
COINS=["BTC","ETH","SOL","HYPE"]
DATA={}
for c in COINS:
    try: DATA[c]=load(c,TF)
    except FileNotFoundError: pass
EMAS=[(9,21),(12,26),(20,50),(21,55),(50,100)]
EXITS=[dict(slMult=1.5,tpMult=3,trailMult=0),dict(slMult=2,tpMult=4,trailMult=0),
       dict(slMult=2,tpMult=0,trailMult=3),dict(slMult=3,tpMult=0,trailMult=4),
       dict(slMult=2.5,tpMult=0,trailMult=0,exitOnCross=True)]
GRID=list(itertools.product(EMAS,[15,20,25],[0,1.0,1.5],[True,False],[True,False],range(len(EXITS)),[True,False]))
CACHE={}
def prep(c,ef,es):
    k=(c,ef,es)
    if k not in CACHE:
        df=DATA[c]; p=dict(DEFAULT,lenFast=ef,lenSlow=es)
        CACHE[k]=(indicators(df,p),htf_trend(df,HTF[TF],50,200))
    return CACHE[k]
def job(g):
    (ef,es),adxm,vm,lf,uh,ex,lo=g
    p=dict(DEFAULT,lenFast=ef,lenSlow=es,adxMin=adxm,volMult=vm,useLongFilter=lf,useHtf=uh,longOnly=lo,**EXITS[ex])
    out={}
    for c,df in DATA.items():
        ind,ht=prep(c,ef,es); n=len(df); cut=int(n*0.65)
        out[c]=(run(df,p,ind,ht,0,cut),run(df,p,ind,ht,cut,n))
    return g,out
if __name__=="__main__":
    with Pool(4) as pool:
        res=pool.map(job,GRID,chunksize=8)
    pickle.dump(res,open(f"grid_{TF}.pkl","wb"))
    print(TF,len(res))
