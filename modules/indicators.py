'''Technical Indicators - MA, EMA, MACD, RSI, BB, ATR, signals'''
import pandas as pd
import numpy as np

def calculate_all_indicators(df):
    df = df.copy()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    ema12 = df["EMA12"]
    ema26 = df["EMA26"]
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    df["BB_Mid"] = df["Close"].rolling(20).mean()
    bb_std = df["Close"].rolling(20).std()
    df["BB_Up"] = df["BB_Mid"] + 2 * bb_std
    df["BB_Low"] = df["BB_Mid"] - 2 * bb_std
    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift(1))
    low_close = abs(df["Low"] - df["Close"].shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()
    df["Vol_MA20"] = df["Volume"].rolling(20).mean()
    return df

def generate_signals(df):
    df = df.copy()
    df["signal"] = "HOLD"
    df["strength"] = ""
    df["score"] = 0
    for i in range(60, len(df)):
        score = 0
        if df["MA5"].iloc[i] > df["MA20"].iloc[i] and df["MA5"].iloc[i-1] <= df["MA20"].iloc[i-1]:
            score += 2
        elif df["MA5"].iloc[i] < df["MA20"].iloc[i] and df["MA5"].iloc[i-1] >= df["MA20"].iloc[i-1]:
            score -= 2
        if df["MACD"].iloc[i] > df["MACD_Signal"].iloc[i] and df["MACD"].iloc[i-1] <= df["MACD_Signal"].iloc[i-1]:
            score += 2
        elif df["MACD"].iloc[i] < df["MACD_Signal"].iloc[i] and df["MACD"].iloc[i-1] >= df["MACD_Signal"].iloc[i-1]:
            score -= 2
        rsi = df["RSI"].iloc[i]
        if not np.isnan(rsi):
            if rsi < 30: score += 1
            elif rsi > 70: score -= 1
        close = df["Close"].iloc[i]
        if not pd.isna(df["BB_Low"].iloc[i]) and close < df["BB_Low"].iloc[i]:
            score += 1
        elif not pd.isna(df["BB_Up"].iloc[i]) and close > df["BB_Up"].iloc[i]:
            score -= 1
        # EMA crossover bonus
        if df["EMA12"].iloc[i] > df["EMA26"].iloc[i] and df["EMA12"].iloc[i-1] <= df["EMA26"].iloc[i-1]:
            score += 2
        elif df["EMA12"].iloc[i] < df["EMA26"].iloc[i] and df["EMA12"].iloc[i-1] >= df["EMA26"].iloc[i-1]:
            score -= 2
        df.at[df.index[i], "score"] = score
        if score >= 3:
            df.at[df.index[i], "signal"] = "BUY"
            df.at[df.index[i], "strength"] = "strong" if score >= 5 else "normal"
        elif score <= -3:
            df.at[df.index[i], "signal"] = "SELL"
            df.at[df.index[i], "strength"] = "strong" if score <= -5 else "normal"
    return df

def analyze_trend(df):
    if len(df) < 20:
        return {"trend": "数据不足", "direction": "无"}
    close = df["Close"].iloc[-1]
    ma20 = df["MA20"].iloc[-1]
    ma60 = df["MA60"].iloc[-1]
    if close > ma20 > ma60:
        trend = "强势上涨"
    elif close > ma20:
        trend = "弱势上涨"
    elif close < ma20 < ma60:
        trend = "强势下跌"
    elif close < ma20:
        trend = "弱势下跌"
    else:
        trend = "Sideways"
    return {"trend": trend, "direction": "Bullish" if close > ma20 else "Bearish"}
