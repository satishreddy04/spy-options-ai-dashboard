import csv
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import analyze
from agents import run_agents

st.set_page_config(page_title="SPY Options AI",layout="wide")
st.title("SPY Options AI Dashboard")
st.caption("Paper-trading decision support — no live broker orders.")
symbol=st.sidebar.selectbox("Underlying",["SPY"])
st.sidebar.button("Refresh now")

try:
    df,d=analyze(symbol); agents=run_agents(df)
    overview,agent_tab,tech_tab,journal_tab=st.tabs(["Overview","Agents","Technicals","Journal"])
    with overview:
        a,b,c,e=st.columns(4)
        a.metric(symbol,f"${d.price:.2f}"); b.metric("Decision",d.action)
        c.metric("Confidence",f"{d.confidence}%"); e.metric("Regime",d.regime)
        if d.action=="CALL": st.success("READY: bullish alignment detected. Paper-trade idea only.")
        elif d.action=="PUT": st.error("READY: bearish alignment detected. Paper-trade idea only.")
        else: st.warning("WAIT / NO TRADE: confirmation is insufficient.")
        x,y,z=st.columns(3)
        x.metric("Invalidation",f"${d.stop:.2f}"); y.metric("Target 1",f"${d.target1:.2f}"); z.metric("Target 2",f"${d.target2:.2f}")
        st.write("**Confirmations**")
        for r in d.reasons: st.write("•",r)
        st.info("Signal is based on the underlying SPY chart, not an options contract. Options-chain/Greeks selection comes in a later stage.")
    with agent_tab:
        st.subheader("Agent consensus")
        rows=[{"Agent":a.name,"Bias":a.bias,"Score":a.score,"Evidence":a.detail} for a in agents]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        directional=[a.score for a in agents if a.name!="Risk"]
        total=sum(directional)
        st.metric("Agent consensus score",total)
        st.caption("Positive = bullish, negative = bearish. Risk is a gate, not a directional vote.")
    with tech_tab:
        st.subheader("EMA + price")
        st.line_chart(df[["Close","ema8","ema20","ema50"]].tail(120))
        last=df.iloc[-1]
        a,b,c,e=st.columns(4)
        a.metric("RSI",f"{last.rsi:.1f}"); b.metric("VWAP",f"${last.vwap:.2f}")
        c.metric("ATR",f"${last.atr:.2f}"); e.metric("MACD",f"{last.macd:.3f}")
    with journal_tab:
        path=Path("data/trades.csv")
        with st.form("paper_trade"):
            note=st.text_input("Trade note")
            submitted=st.form_submit_button("Record current idea")
            if submitted:
                path.parent.mkdir(exist_ok=True); new=not path.exists()
                with path.open("a",newline="") as f:
                    w=csv.writer(f)
                    if new:w.writerow(["timestamp","symbol","action","price","confidence","regime","stop","target1","target2","note"])
                    w.writerow([datetime.now().isoformat(),d.symbol,d.action,d.price,d.confidence,d.regime,d.stop,d.target1,d.target2,note])
                st.success("Paper-trade idea recorded.")
        if path.exists():
            st.dataframe(pd.read_csv(path).tail(50),use_container_width=True,hide_index=True)
except Exception as exc:
    st.error(f"Analysis unavailable: {exc}")
    st.info("Free market-data feeds may be delayed or temporarily unavailable.")
