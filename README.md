# SPY Options AI Dashboard

Paper-trading decision-support dashboard inspired by the architecture of JSoulas91/spy-options-bot.

## V1
- SPY market data via yfinance
- EMA 8/20/50, RSI, MACD, ATR, VWAP
- Trend/regime classification
- Confidence score
- CALL / PUT / NO TRADE decision
- ATR-based stop and targets
- Streamlit dashboard
- Paper trade journal (CSV)

This project does **not** place live broker orders.

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Market data from free sources can be delayed or incomplete. Validate signals with paper trading before relying on them.
