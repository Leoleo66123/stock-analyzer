'''Anomaly Detector - z-score, volume spike, volatility jump, gap detection'''
import pandas as pd
import numpy as np

def detect_anomalies(df):
    if len(df) < 20:
        return {"status": "normal", "status_text": "数据不足", "signal_weight": 1.0, "alerts": []}
    alerts = []
    weight = 1.0
    close = df["Close"].iloc[-1]
    vol = df["Volume"].iloc[-1]
    atr = df["ATR"].iloc[-1] if "ATR" in df.columns else 0

    # z-score extreme (daily return)
    rets = df["Close"].pct_change().dropna()
    if len(rets) > 10:
        z = (rets.iloc[-1] - rets.mean()) / (rets.std() or 1)
        if abs(z) > 2.5:
            direction = "暴涨" if z > 0 else "暴跌"
            alerts.append(f"{direction}(z={z:.1f})")
            weight *= 0.6

    # volume spike
    vol_ma = df["Volume"].rolling(20).mean().iloc[-1]
    if vol_ma > 0 and vol > vol_ma * 2.5:
        alerts.append(f"成交量异常({vol/vol_ma:.1f}倍)")
        weight *= 0.7

    # volatility jump
    if "volatility" in df.columns:
        vol_20 = df["volatility"].rolling(20).mean().iloc[-1]
        cur_vol = df["volatility"].iloc[-1]
        if vol_20 > 0 and cur_vol > vol_20 * 1.8:
            alerts.append(f"波动率跳变({cur_vol/vol_20:.1f}倍)")
            weight *= 0.7

    # gap detection
    if len(df) >= 2:
        gap = abs(df["Open"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]
        if gap > 0.02:
            direction = "向上跳空" if df["Open"].iloc[-1] > df["Close"].iloc[-2] else "向下跳空"
            alerts.append(f"{direction} {gap*100:.1f}%")
            weight *= 0.8

    weight = max(weight, 0.2)
    if alerts:
        status = "anomaly"
        status_text = "; ".join(alerts)
    else:
        status = "normal"
        status_text = "未检测到异常"
    return {"status": status, "status_text": status_text, "signal_weight": round(weight, 2), "alerts": alerts}