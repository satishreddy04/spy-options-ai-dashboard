from dataclasses import dataclass
from datetime import datetime, timezone
import re
import yfinance as yf

POS={"beat","beats","gain","gains","rally","surge","strong","growth","optimism","record","upgrade","cooling","cut"}
NEG={"miss","misses","loss","losses","drop","drops","selloff","weak","recession","downgrade","inflation","war","tariff","risk"}

@dataclass
class IntelResult:
    name:str; bias:str; score:int; detail:str

def _headline_score(text):
    words=set(re.findall(r"[a-z]+",text.lower()))
    return len(words&POS)-len(words&NEG)

def news_sentiment(symbol="SPY"):
    try:
        news=(yf.Ticker(symbol).news or [])[:15]
        scores=[]; titles=[]
        for n in news:
            content=n.get("content",n) if isinstance(n,dict) else {}
            title=content.get("title") or n.get("title","")
            if title:
                scores.append(_headline_score(title)); titles.append(title)
        total=sum(scores)
        bias="BULLISH" if total>=2 else "BEARISH" if total<=-2 else "NEUTRAL"
        return IntelResult("News",bias,max(-3,min(3,total)),f"{len(titles)} recent headlines scored"),titles[:8]
    except Exception as e:
        return IntelResult("News","UNKNOWN",0,f"Unavailable: {e}"),[]

def event_risk():
    # Conservative manual gate until a licensed calendar API is configured.
    return IntelResult("Events","MANUAL CHECK",0,"Economic calendar API not configured; verify CPI/FOMC/jobs events before trading.")

def social_sentiment():
    # Do not fabricate social sentiment without an authenticated source.
    return IntelResult("Social","UNAVAILABLE",0,"No authenticated social-data provider configured.")

def run_intelligence(symbol="SPY"):
    news,headlines=news_sentiment(symbol)
    return [news,event_risk(),social_sentiment()],headlines

def final_gate(direction, confidence, agents, intel, option_pick=None):
    if direction=="NO TRADE":
        return "NO TRADE","Underlying confirmations are insufficient."
    directional=sum(a.score for a in agents if a.name!="Risk")
    news=next((x for x in intel if x.name=="News"),None)
    aligned_news=(news and ((direction=="CALL" and news.score>=0) or (direction=="PUT" and news.score<=0)))
    option_ok=option_pick is not None and getattr(option_pick,"score",0)>=55
    confirmations=sum([abs(directional)>=2, confidence>=68, bool(aligned_news), option_ok])
    if confirmations>=4: return "READY","Technical, confidence, news and options-liquidity gates align."
    if confirmations>=2: return "WAIT","Some gates align, but confirmation is incomplete."
    return "NO TRADE","Too few independent confirmations."
