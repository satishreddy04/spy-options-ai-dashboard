import csv
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import analyze
from agents import run_agents
from options_engine import select_contract
from intelligence import run_intelligence, final_gate

st.set_page_config(page_title="SPY Options AI",layout="wide")
st.title("SPY Options AI Dashboard")
st.caption("Paper-trading decision support — no live broker orders.")
symbol=st.sidebar.selectbox("Underlying",["SPY"])
min_dte=st.sidebar.number_input("Min DTE",1,30,2); max_dte=st.sidebar.number_input("Max DTE",2,45,14)
target_delta=st.sidebar.slider("Target |delta|",0.20,0.70,0.40,0.05); st.sidebar.button("Refresh now")

try:
    df,d=analyze(symbol); agents=run_agents(df); intel,headlines=run_intelligence(symbol)
    pick=None; candidates=pd.DataFrame()
    if d.action!="NO TRADE":
        try: pick,candidates=select_contract(symbol,d.action,d.price,int(min_dte),int(max_dte),float(target_delta))
        except Exception: pass
    gate,gate_reason=final_gate(d.action,d.confidence,agents,intel,pick)
    overview,agent_tab,intel_tab,options_tab,tech_tab,journal_tab=st.tabs(["Overview","Agents","News & Events","Options","Technicals","Journal"])
    with overview:
        a,b,c,e=st.columns(4); a.metric(symbol,f"${d.price:.2f}"); b.metric("Direction",d.action); c.metric("Confidence",f"{d.confidence}%"); e.metric("FINAL",gate)
        if gate=="READY": st.success("READY — "+gate_reason)
        elif gate=="WAIT": st.warning("WAIT — "+gate_reason)
        else: st.error("NO TRADE — "+gate_reason)
        st.caption("READY is a paper-trading confirmation, not a recommendation or guarantee.")
        x,y,z=st.columns(3); x.metric("Underlying invalidation",f"${d.stop:.2f}"); y.metric("Target 1",f"${d.target1:.2f}"); z.metric("Target 2",f"${d.target2:.2f}")
        rows=[]
        for a in agents: rows.append({"Check":a.name,"State":a.bias,"Evidence":a.detail})
        for i in intel: rows.append({"Check":i.name,"State":i.bias,"Evidence":i.detail})
        rows.append({"Check":"Options liquidity","State":"PASS" if pick and pick.score>=55 else "WAIT","Evidence":f"Contract score {pick.score}%" if pick else "No candidate"})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    with agent_tab:
        st.dataframe(pd.DataFrame([{"Agent":a.name,"Bias":a.bias,"Score":a.score,"Evidence":a.detail} for a in agents]),use_container_width=True,hide_index=True)
    with intel_tab:
        st.subheader("News sentiment")
        for i in intel:
            st.write(f"**{i.name}: {i.bias}** — {i.detail}")
        if headlines:
            st.write("Recent headlines used:")
            for h in headlines: st.write("•",h)
        st.warning("Economic-event and social sentiment gates intentionally remain manual/unavailable until authenticated data providers are configured. The app will not invent those signals.")
    with options_tab:
        if d.action=="NO TRADE": st.warning("No contract selected because direction is NO TRADE.")
        elif pick:
            a,b,c,e=st.columns(4); a.metric("Expiration",pick.expiration or "—"); b.metric("Type",pick.option_type or "—"); c.metric("Strike",f"${pick.strike:.2f}"); e.metric("Contract score",f"{pick.score}%")
            a,b,c,e=st.columns(4); a.metric("Bid",f"${pick.bid:.2f}"); b.metric("Ask",f"${pick.ask:.2f}"); c.metric("Mid",f"${pick.mid:.2f}"); e.metric("Est. |delta|",f"{abs(pick.delta_est):.2f}")
            st.write(f"OI **{pick.open_interest:,}** | Volume **{pick.volume:,}** | IV **{pick.iv:.1%}** | Approx debit at mid **${pick.max_debit:,.0f}/contract**")
            st.info("Yahoo/OPRA options data may be delayed. Delta is locally estimated; verify contract and quote at your broker.")
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
                    if new:w.writerow(["timestamp","symbol","action","price","confidence","final_gate","note"])
                    w.writerow([datetime.now().isoformat(),d.symbol,d.action,d.price,d.confidence,gate,note])
                st.success("Paper-trade idea recorded.")
        if path.exists(): st.dataframe(pd.read_csv(path).tail(50),use_container_width=True,hide_index=True)
except Exception as exc:
    st.error(f"Analysis unavailable: {exc}")
