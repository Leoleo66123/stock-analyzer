'''Market Regime Detector'''
import numpy as np

def detect_market_regime(df):
    if len(df) < 60:
        return {"regime": "未知", "label": "数据不足", "strategy": "持有观望"}
    close = df["Close"]
    ma20 = df.get("MA20", close.rolling(20).mean())
    ma60 = df.get("MA60", close.rolling(60).mean())
    ret_5 = close.pct_change(5).iloc[-1]
    ret_20 = close.pct_change(20).iloc[-1]
    ret_60 = close.pct_change(60).iloc[-1] if len(close) >= 60 else 0
    vol_20 = close.pct_change().rolling(20).std().iloc[-1]
    vol_60 = close.pct_change().rolling(60).std().iloc[-1] if len(close) >= 60 else vol_20
    cur = close.iloc[-1]
    ma20_val = ma20.iloc[-1]
    ma60_val = ma60.iloc[-1] if len(ma60) > 0 else ma20_val

    # Check trend strength via slope and position
    ma20_slope = (ma20.iloc[-1] / ma20.iloc[-10] - 1) if len(ma20) >= 10 else 0
    above_ma20 = cur > ma20_val
    above_ma60 = cur > ma60_val
    ma_bullish = ma20_val > ma60_val

    if above_ma20 and above_ma60 and ma_bullish and ret_20 > 0.08:
        regime = "strong_bull"
        label = "强势上涨"
        strategy = "逢低买入，移动止损，满仓"
    elif above_ma20 and ma_bullish and ret_20 > 0.02:
        regime = "bullish"
        label = "温和上涨"
        strategy = "持多做多，适度加仓"
    elif above_ma20 and above_ma60 and ma20_slope > 0.005:
        regime = "weak_bull"
        label = "弱势上涨"
        strategy = "谨慎做多，严格止损"
    elif not above_ma20 and not above_ma60 and not ma_bullish and ret_20 < -0.08:
        regime = "strong_bear"
        label = "强势下跌"
        strategy = "做空或空仓，避免做多"
    elif not above_ma20 and ret_20 < -0.03:
        regime = "bearish"
        label = "持续下跌"
        strategy = "减仓或空仓，不宜抄底"
    elif not above_ma20 and ma20_slope < -0.003:
        regime = "weak_bear"
        label = "弱势下跌"
        strategy = "小仓位做空或观望"
    elif vol_20 > vol_60 * 1.5:
        regime = "high_vol"
        label = "高波动"
        strategy = "减仓，放宽止损"
    elif abs(ret_5) < 0.01 and abs(ma20_slope) < 0.003:
        regime = "sideways"
        label = "横盘震荡"
        strategy = "高抛低吸或等待突破"
    else:
        regime = "mixed"
        label = "方向不明"
        strategy = "轻仓观望，等待信号"

    return {"regime": regime, "label": label, "strategy": strategy}