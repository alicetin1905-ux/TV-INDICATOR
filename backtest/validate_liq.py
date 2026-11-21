import json, time, urllib.request, numpy as np, pandas as pd
def get(url):
    for i in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl/8.0"}),timeout=20))
        except Exception: time.sleep(1+i)
    return {}
ctval={"BTC":0.01,"ETH":0.1,"SOL":1,"HYPE":0.1}
allr=[]
for coin in ["BTC","ETH","SOL","HYPE"]:
    oi=[];end=None
    for _ in range(4):
        d=get(f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history?instId={coin}-USDT-SWAP&period=5m&limit=100"+(f"&end={end}" if end else "")).get("data",[])
        if not d: break
        oi+=d; end=d[-1][0]; time.sleep(.2)
    oi=pd.DataFrame(oi,columns=["ts","a","b","oi"]).drop_duplicates("ts"); oi["ts"]=pd.to_datetime(oi.ts.astype("int64"),unit="ms"); oi["oi"]=oi.oi.astype(float); oi=oi.sort_values("ts")
    k=[];after=None
    for _ in range(4):
        d=get(f"https://www.okx.com/api/v5/market/history-candles?instId={coin}-USDT-SWAP&bar=5m&limit=100"+(f"&after={after}" if after else "")).get("data",[])
        if not d: break
        k+=d; after=d[-1][0]; time.sleep(.2)
    k=pd.DataFrame(k).iloc[:,:5]; k.columns=["ts","o","h","l","c"]; k["ts"]=pd.to_datetime(k.ts.astype("int64"),unit="ms"); k[["o","h","l","c"]]=k[["o","h","l","c"]].astype(float); k=k.sort_values("ts")
    lq=pd.read_csv(f"data/{coin}_LIQ.csv",parse_dates=["ts"]); lq["usd"]*=ctval[coin]; lq["bar"]=lq.ts.dt.floor("5min")
    L=lq.pivot_table(index="bar",columns="posSide",values="usd",aggfunc="sum").fillna(0)
    for sh,name in [(0,"oi[t]-oi[t-1]"),(-1,"oi[t+1]-oi[t]")]:
        o=oi.set_index("ts").oi.shift(sh)
        df=k.set_index("ts").join(o.rename("oi")).join(L).fillna({"long":0,"short":0}).dropna()
        df=df[(df.index>=lq.ts.min())&(df.index<=lq.ts.max())]
        df["doi"]=df.oi.pct_change(); df["ret"]=df.c/df.o-1; df["liq"]=df.long+df.short
        df=df.dropna()
        c1=np.corrcoef(df.doi,df.liq)[0,1]
        print(f"{coin:5} {name:15} corr(dOI, liq$)={c1:+.3f}  n={len(df)}")
    # proxy test with best alignment (choose per printed result later)
    allr.append((coin,k,oi,L))
pd.to_pickle(allr,"liq5m.pkl")
