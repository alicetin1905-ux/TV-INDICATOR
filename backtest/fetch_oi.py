import json, time, urllib.request
import pandas as pd
def get(url):
    for i in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl/8.0"}),timeout=20))
        except Exception: time.sleep(1+i)
    return {}
for coin in ["BTC","ETH","SOL","HYPE"]:
    rows=[]; end=None
    while True:
        u=f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history?instId={coin}-USDT-SWAP&period=4H&limit=100"+(f"&end={end}" if end else "")
        d=get(u).get("data",[])
        if not d: break
        rows+=d
        nxt=d[-1][0]
        if end==nxt: break
        end=nxt; time.sleep(0.25)
        if len(rows)>12000: break
    df=pd.DataFrame(rows,columns=["ts","oi","oiCcy","oiUsd"]).drop_duplicates("ts")
    df["ts"]=pd.to_datetime(df.ts.astype("int64"),unit="ms"); df["oiUsd"]=df.oiUsd.astype(float)
    df=df.sort_values("ts")[["ts","oiUsd"]]
    df.to_csv(f"data/{coin}_OI_4H.csv",index=False)
    print(coin,len(df),df.ts.min(),df.ts.max(),flush=True)
