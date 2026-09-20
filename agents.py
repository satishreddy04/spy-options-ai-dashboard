from dataclasses import dataclass
import pandas as pd

@dataclass
class AgentResult:
    name: str
    bias: str
    score: int
    detail: str

def technical_agent(df: pd.DataFrame) -> AgentResult:
    x=df.iloc[-1]; score=0; notes=[]
    if x.ema8>x.ema20>x.ema50: score+=2; notes.append("EMA 8>20>50")
    elif x.ema8<x.ema20<x.ema50: score-=2; notes.append("EMA 8<20<50")
    if x.Close>x.vwap: score+=1; notes.append("above VWAP")
    else: score-=1; notes.append("below VWAP")
    if x.macd>x.macd_signal: score+=1; notes.append("MACD positive")
    else: score-=1; notes.append("MACD negative")
    bias="BULLISH" if score>=2 else "BEARISH" if score<=-2 else "NEUTRAL"
    return AgentResult("Technical",bias,score,", ".join(notes))

def levels_agent(df: pd.DataFrame) -> AgentResult:
    today=df.index[-1].date()
    days=sorted(set(df.index.date))
    prior=[d for d in days if d<today]
    if not prior: return AgentResult("Levels","NEUTRAL",0,"Need prior session")
    p=df[[i.date()==prior[-1] for i in df.index]]
    pdh=float(p.High.max()); pdl=float(p.Low.min()); px=float(df.Close.iloc[-1])
    score=1 if px>pdh else -1 if px<pdl else 0
    bias="BULLISH" if score>0 else "BEARISH" if score<0 else "NEUTRAL"
    return AgentResult("PDH/PDL",bias,score,f"PDH {pdh:.2f} | PDL {pdl:.2f} | price {px:.2f}")

def regime_agent(df: pd.DataFrame) -> AgentResult:
    x=df.iloc[-1]
    gap=abs(float(x.ema8-x.ema50))/float(x.Close)*100
    if gap<0.12: return AgentResult("Regime","NEUTRAL",0,f"CHOP/MIXED, EMA spread {gap:.2f}%")
    bull=x.ema8>x.ema20>x.ema50
    return AgentResult("Regime","BULLISH" if bull else "BEARISH",1 if bull else -1,f"TREND, EMA spread {gap:.2f}%")

def risk_agent(df: pd.DataFrame) -> AgentResult:
    x=df.iloc[-1]; atr=float(x.atr); px=float(x.Close)
    pct=atr/px*100 if px else 0
    if pct>0.8: return AgentResult("Risk","CAUTION",0,f"Elevated ATR {pct:.2f}%")
    return AgentResult("Risk","OK",0,f"ATR {pct:.2f}%")

def run_agents(df):
    return [technical_agent(df),levels_agent(df),regime_agent(df),risk_agent(df)]
