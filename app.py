import csv
from datetime import datetime
from pathlib import Path
import streamlit as st
from engine import analyze

st.set_page_config(page_title="SPY Options AI", layout="wide")
st.title("SPY Options AI Dashboard")
st.caption("Decision support + paper trading. No live orders.")

symbol = st.sidebar.selectbox("Underlying", ["SPY"])
refresh = st.sidebar.button("Refresh analysis")

try:
    df, d = analyze(symbol)
    a,b,c,dcol = st.columns(4)
    a.metric("SPY", f"${d.price:.2f}")
    b.metric("Decision", d.action)
    c.metric("Confidence", f"{d.confidence}%")
    dcol.metric("Regime", d.regime)

    if d.action == "NO TRADE":
        st.warning("NO TRADE — conditions are not sufficiently aligned.")
    elif d.action == "CALL":
        st.success("Bullish setup detected — paper-trade CALL idea only.")
    else:
        st.error("Bearish setup detected — paper-trade PUT idea only.")

    x,y,z = st.columns(3)
    x.metric("Stop / invalidation", f"${d.stop:.2f}")
    y.metric("Target 1", f"${d.target1:.2f}")
    z.metric("Target 2", f"${d.target2:.2f}")

    st.subheader("Why")
    for reason in d.reasons:
        st.write("•", reason)

    st.subheader("Price")
    st.line_chart(df[["Close", "ema8", "ema20", "ema50"]].tail(120))

    st.subheader("Paper Trade Journal")
    with st.form("paper_trade"):
        note = st.text_input("Trade note")
        submitted = st.form_submit_button("Record current idea")
        if submitted:
            path = Path("data/trades.csv")
            path.parent.mkdir(exist_ok=True)
            new = not path.exists()
            with path.open("a", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["timestamp","symbol","action","price","confidence","regime","stop","target1","target2","note"])
                w.writerow([datetime.now().isoformat(), d.symbol, d.action, d.price, d.confidence, d.regime, d.stop, d.target1, d.target2, note])
            st.success("Paper-trade idea recorded.")
except Exception as e:
    st.error(f"Analysis unavailable: {e}")
    st.info("Try again during/after a market session. Free market-data feeds can be delayed.")
