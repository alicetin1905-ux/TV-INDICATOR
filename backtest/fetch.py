import json, time, urllib.request, sys, os
import pandas as pd
BASE="https://www.okx.com/api/v5/market/history-candles"
def fetch(inst, bar, days):
    end_ms = int(time.time()*1000); start_ms = end_ms - days*86400*1000
    rows=[]; after=None; d={}
    while True:
        url=f"{BASE}?instId={inst}&bar={bar}&limit=100"+(f"&after={after}" if after else "")
        for i in range(5):
            try:
                d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl/8.0"}), timeout=20)); break
            except Exception as e:
                time.sleep(1+i)
        data=d.get("data",[])
        if not data: break
        rows+=data; after=data[-1][0]
        if int(after)<start_ms: break
        time.sleep(0.12)
    df=pd.DataFrame(rows,columns=["ts","o","h","l","c","vol","volCcy","volQuote","confirm"])
    df=df[df.confirm=="1"]
    df["ts"]=pd.to_datetime(df.ts.astype("int64"),unit="ms")
    df=df.astype({"o":float,"h":float,"l":float,"c":float,"volQuote":float}).sort_values("ts").drop_duplicates("ts")
    df=df[df.ts>=pd.to_datetime(start_ms,unit="ms")]
    return df[["ts","o","h","l","c","volQuote"]].rename(columns={"volQuote":"v"})
for coin in ["BTC","ETH","SOL","HYPE"]:
    for bar,days in [("1H",730),("4H",1460),("15m",180)]:
        df=fetch(f"{coin}-USDT",bar,days)
        df.to_csv(f"data/{coin}_{bar}.csv",index=False)
        print(coin,bar,len(df),df.ts.min(),df.ts.max(),flush=True)
