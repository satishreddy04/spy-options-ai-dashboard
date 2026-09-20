import csv
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import analyze
from agents import run_agents
from options_engine import select_contract

st.set_page_config(page_title="SPY Options AI",layout="wide")
st.title("SPY Options AI Dashboard")
st.caption("Paper-trading decision support — no live broker orders.")
symbol=st.sidebar.selectbox("Underlying",["SPY"])
min_dte=st.sidebar.number_input("Min DTE",1,30,2)
max_dte=st.sidebar.number_input("Max DTE",2,45,14)
target_delta=st.sidebar.slider("Target |delta|",0.20,0.70,0.40,0.05)
st.sidebar.button("Refresh now")

try:
    df,d=analyze(symbol); agents=run_agents(df)
    overview,agent_tab,options_tab,tech_tab,journal_tab=st.tabs(["Overview","Agents","Options","Technicals","Journal"])
    with overview:
        a,b,c,e=st.columns(4); a.metric(symbol,f"${d.price:.2f}"); b.metric("Decision",d.action); c.metric("Confidence",f"{d.confidence}%"); e.metric("Regime",d.regime)
        if d.action=="CALL": st.success("READY: bullish alignment. Review Options tab before any paper trade.")
        elif d.action=="PUT": st.error("READY: bearish alignment. Review Options tab before any paper trade.")
        else: st.warning("WAIT / NO TRADE: confirmation is insufficient.")
        x,y,z=st.columns(3); x.metric("Underlying invalidation",f"${d.stop:.2f}"); y.metric("Underlying target 1",f"${d.target1:.2f}"); z.metric("Underlying target 2",f"${d.target2:.2f}")
        for r in d.reasons: st.write("•",r)
    with agent_tab:
        rows=[{"Agent":a.name,"Bias":a.bias,"Score":a.score,"Evidence":a.detail} for a in agents]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        st.metric("Agent consensus score",sum(a.score for a in agents if a.name!="Risk"))
    with options_tab:
        st.subheader("Options contract candidate")
        if d.action=="NO TRADE":
            st.warning("No contract selected because master signal is NO TRADE.")
        else:
            with st.spinner("Loading options chain..."):
                pick,candidates=select_contract(symbol,d.action,d.price,int(min_dte),int(max_dte),float(target_delta))
            if pick:
                a,b,c,e=st.columns(4); a.metric("Expiration",pick.expiration or "—"); b.metric("Type",pick.option_type or "—"); c.metric("Strike",f"${pick.strike:.2f}"); e.metric("Contract score",f"{pick.score}%")
                a,b,c,e=st.columns(4); a.metric("Bid",f"${pick.bid:.2f}"); b.metric("Ask",f"${pick.ask:.2f}"); c.metric("Mid",f"${pick.mid:.2f}"); e.metric("Est. |delta|",f"{abs(pick.delta_est):.2f}")
                st.write(f"Open interest: **{pick.open_interest:,}** | Volume: **{pick.volume:,}** | IV: **{pick.iv:.1%}** | Approx debit at mid: **${pick.max_debit:,.0f}/contract**")
                st.info("Delta is estimated locally and quotes come from yfinance. Treat this as a candidate/ranking tool, not an executable quote or broker-grade Greeks.")
                if not candidates.empty: st.dataframe(candidates,use_container_width=True,hide_index=True)
            else: st.warning("No usable contract candidate returned.")
    with tech_tab:
        st.line_chart(df[["Close","ema8","ema20","ema50"]].tail(120)); last=df.iloc[-1]
        a,b,c,e=st.columns(4); a.metric("RSI",f"{last.rsi:.1f}"); b.metric("VWAP",f"${last.vwap:.2f}"); c.metric("ATR",f"${last.atr:.2f}"); e.metric("MACD",f"{last.macd:.3f}")
    with journal_tab:
        path=Path("data/trades.csv")
        with st.form("paper_trade"):
            note=st.text_input("Trade note"); submitted=st.form_submit_button("Record current idea")
            if submitted:
                path.parent.mkdir(exist_ok=True); new=not path.exists()
                with path.open("a",newline="") as f:
                    w=csv.writer(f)
                    if new:w.writerow(["timestamp","symbol","action","price","confidence","regime","stop","target1","target2","note"])
                    w.writerow([datetime.now().isoformat(),d.symbol,d.action,d.price,d.confidence,d.regime,d.stop,d.target1,d.target2,note])
                st.success("Paper-trade idea recorded.")
        if path.exists(): st.dataframe(pd.read_csv(path).tail(50),use_container_width=True,hide_index=True)
except Exception as exc:
    st.error(f"Analysis unavailable: {exc}")
    st.info("Free yfinance market/options data can be delayed, incomplete, or temporarily unavailable.")
