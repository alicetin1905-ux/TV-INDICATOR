import json, time, urllib.request, pandas as pd
def get(url):
    for i in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl/8.0"}),timeout=20))
        except Exception: time.sleep(1+i)
    return {}
ctval={"BTC":0.01,"ETH":0.1,"SOL":1,"HYPE":0.1}
for coin in ["BTC","ETH","SOL","HYPE"]:
    rows=[]; after=None
    for _ in range(400):
        u=f"https://www.okx.com/api/v5/public/liquidation-orders?instType=SWAP&uly={coin}-USDT&state=filled&limit=100"+(f"&after={after}" if after else "")
        d=get(u).get("data",[])
        det=[x for blk in d for x in blk["details"]]
        if not det: break
        rows+=det
        last=min(int(x["ts"]) for x in det)
        if after==str(last): break
        after=str(last); time.sleep(0.2)
    df=pd.DataFrame(rows).drop_duplicates()
    df["ts"]=pd.to_datetime(df.ts.astype("int64"),unit="ms")
    df["usd"]=df.sz.astype(float)*df.bkPx.astype(float)
    df.to_csv(f"data/{coin}_LIQ.csv",index=False)
    print(coin,len(df),df.ts.min(),df.ts.max(), "longs $%.1fM shorts $%.1fM"%(df[df.posSide=="long"].usd.sum()/1e6*ctval[coin], df[df.posSide=="short"].usd.sum()/1e6*ctval[coin]),flush=True)
