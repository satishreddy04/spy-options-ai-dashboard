from dataclasses import dataclass
import numpy as np
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

@dataclass
class Decision:
    symbol: str
    price: float
    action: str
    confidence: int
    regime: str
    stop: float
    target1: float
    target2: float
    reasons: list[str]

def load_data(symbol="SPY", period="5d", interval="5m"):
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError("No market data returned.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna().copy()

def analyze(symbol="SPY"):
    df = load_data(symbol)
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    df["ema8"] = EMAIndicator(c, 8).ema_indicator()
    df["ema20"] = EMAIndicator(c, 20).ema_indicator()
    df["ema50"] = EMAIndicator(c, 50).ema_indicator()
    df["rsi"] = RSIIndicator(c, 14).rsi()
    macd = MACD(c)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["atr"] = AverageTrueRange(h, l, c, 14).average_true_range()
    typical = (h + l + c) / 3
    df["vwap"] = (typical * v).cumsum() / v.replace(0, np.nan).cumsum()

    x = df.iloc[-1]
    bull = 0
    bear = 0
    reasons = []

    if x.ema8 > x.ema20 > x.ema50:
        bull += 2; reasons.append("EMA stack bullish")
    elif x.ema8 < x.ema20 < x.ema50:
        bear += 2; reasons.append("EMA stack bearish")

    if x.Close > x.vwap:
        bull += 1; reasons.append("Price above VWAP")
    else:
        bear += 1; reasons.append("Price below VWAP")

    if x.macd > x.macd_signal:
        bull += 1; reasons.append("MACD bullish")
    else:
        bear += 1; reasons.append("MACD bearish")

    if 52 <= x.rsi <= 70:
        bull += 1; reasons.append(f"RSI supports bullish momentum ({x.rsi:.1f})")
    elif 30 <= x.rsi <= 48:
        bear += 1; reasons.append(f"RSI supports bearish momentum ({x.rsi:.1f})")

    spread = bull - bear
    if spread >= 3:
        action = "CALL"
    elif spread <= -3:
        action = "PUT"
    else:
        action = "NO TRADE"

    confidence = min(95, 50 + abs(spread) * 9) if action != "NO TRADE" else max(20, 50 - abs(spread) * 8)
    regime = "BULL TREND" if bull >= 4 else "BEAR TREND" if bear >= 4 else "CHOP / MIXED"
    price, atr = float(x.Close), float(x.atr)

    if action == "CALL":
        stop, t1, t2 = price - atr, price + atr, price + 2 * atr
    elif action == "PUT":
        stop, t1, t2 = price + atr, price - atr, price - 2 * atr
    else:
        stop = t1 = t2 = price

    return df, Decision(symbol, price, action, int(confidence), regime, stop, t1, t2, reasons)
