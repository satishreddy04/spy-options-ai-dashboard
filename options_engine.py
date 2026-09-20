from dataclasses import dataclass
from datetime import datetime
import math
import pandas as pd
import yfinance as yf

@dataclass
class OptionPick:
    status:str; expiration:str; option_type:str; strike:float; bid:float; ask:float
    mid:float; volume:int; open_interest:int; iv:float; delta_est:float
    max_debit:float; score:int; reason:str

def _norm(v, default=0):
    try:
        if pd.isna(v): return default
        return v
    except Exception: return default

def _delta_proxy(spot,strike,iv,dte,is_call):
    # Approximation for ranking only; not broker-grade Greeks.
    if iv<=0 or dte<=0: return 0.5 if is_call else -0.5
    t=dte/365
    z=(math.log(spot/strike)+(0.5*iv*iv)*t)/(iv*math.sqrt(t))
    cdf=0.5*(1+math.erf(z/math.sqrt(2)))
    return cdf if is_call else cdf-1

def select_contract(symbol, direction, spot, min_dte=2, max_dte=14, target_delta=.40):
    if direction not in ("CALL","PUT"):
        return None, pd.DataFrame()
    ticker=yf.Ticker(symbol)
    expiries=list(ticker.options or [])
    today=datetime.now().date()
    eligible=[]
    for e in expiries:
        dte=(datetime.strptime(e,"%Y-%m-%d").date()-today).days
        if min_dte<=dte<=max_dte: eligible.append((e,dte))
    if not eligible:
        return OptionPick("NO CONTRACT","","",0,0,0,0,0,0,0,0,0,0,"No expiration in selected DTE window"),pd.DataFrame()
    exp,dte=eligible[0]
    chain=ticker.option_chain(exp)
    table=(chain.calls if direction=="CALL" else chain.puts).copy()
    if table.empty: return None,table
    is_call=direction=="CALL"
    table["bid"]=table["bid"].fillna(0); table["ask"]=table["ask"].fillna(0)
    table["mid"]=(table["bid"]+table["ask"])/2
    table["volume"]=table["volume"].fillna(0); table["openInterest"]=table["openInterest"].fillna(0)
    table["impliedVolatility"]=table["impliedVolatility"].fillna(0)
    table["delta_est"]=table.apply(lambda r:_delta_proxy(spot,float(r.strike),float(r.impliedVolatility),dte,is_call),axis=1)
    table["delta_gap"]=(table["delta_est"].abs()-target_delta).abs()
    table["spread_pct"]=(table["ask"]-table["bid"])/table["mid"].replace(0,float("nan"))
    liquid=table[(table.ask>0)&(table.bid>=0)&(table.openInterest>=50)&(table.spread_pct<=.25)].copy()
    pool=liquid if not liquid.empty else table[table.ask>0].copy()
    if pool.empty: return None,table
    pool["rank"]=pool["delta_gap"]+pool["spread_pct"].fillna(1)*.25-(pool["openInterest"].clip(upper=5000)/5000)*.05
    r=pool.sort_values("rank").iloc[0]
    score=max(0,min(100,int(100-r.delta_gap*120-min(float(_norm(r.spread_pct,1)),1)*25)))
    mid=float(r.mid); max_debit=mid*100
    pick=OptionPick("CANDIDATE",exp,direction,float(r.strike),float(r.bid),float(r.ask),mid,int(r.volume),int(r.openInterest),float(r.impliedVolatility),float(r.delta_est),max_debit,score,"Ranked by delta proximity, spread and open interest")
    cols=["contractSymbol","strike","bid","ask","mid","volume","openInterest","impliedVolatility","delta_est","spread_pct"]
    return pick,pool.sort_values("rank")[cols].head(10)
