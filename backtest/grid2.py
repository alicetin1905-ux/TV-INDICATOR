import itertools, pickle
from multiprocessing import Pool
import numpy as np
from engine2 import *
COINS=["BTC","ETH","SOL","HYPE"]
D={c:load(c,"4H") for c in COINS}
BTC=D["BTC"]
PRE={}
for c in COINS:
    df=D[c]
    PRE[c]=dict(ind=indicators(df,BASE),ht=htf_trend(df,"1D",50,200),
                b4=btc_trend(BTC,df.ts.values,None),b1=btc_trend(BTC,df.ts.values,"1D"))
RE=[dict(reEntry=False)]+[dict(reEntry=True,reStrictHtf=a,reNeedRibbon=b,reNeedAdx=d,reMax=m)
    for a,b,d,m in itertools.product([True,False],[True,False],[True,False],[1,2,99])]
GRID=list(itertools.product(["off","4H","1D"],range(len(RE)),[0,4,5]))
def job(g):
    bf,ri,tb=g
    p=dict(BASE,useBtc=bf!="off",trailBull=tb,**RE[ri])
    out={}
    for c in COINS:
        pr=PRE[c]; df=D[c]; n=len(df); cut=int(n*.65)
        bt=None if bf=="off" else (pr["b4"] if bf=="4H" else pr["b1"])
        out[c]=(stats2(run2(df,p,pr["ind"],pr["ht"],bt,0,cut)),stats2(run2(df,p,pr["ind"],pr["ht"],bt,cut,n)),stats2(run2(df,p,pr["ind"],pr["ht"],bt)))
    return g,out
if __name__=="__main__":
    with Pool(4) as pool: res=pool.map(job,GRID)
    pickle.dump((res,RE),open("grid2.pkl","wb")); print(len(res))
