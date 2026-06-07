'''A-Share data via Yahoo Finance (primary) + AkShare (fallback)'''
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

_ashare_cache = {}

A_SHARE_POPULAR = [
    {"symbol": "600519.SH", "name": "贵州茅台", "market": "CN"},
    {"symbol": "000858.SZ", "name": "五粮液", "market": "CN"},
    {"symbol": "300750.SZ", "name": "宁德时代", "market": "CN"},
    {"symbol": "601318.SH", "name": "中国平安", "market": "CN"},
    {"symbol": "000333.SZ", "name": "美的集团", "market": "CN"},
    {"symbol": "600036.SH", "name": "招商银行", "market": "CN"},
    {"symbol": "002594.SZ", "name": "比亚迪", "market": "CN"},
    {"symbol": "688981.SH", "name": "中芯国际", "market": "CN"},
]

def is_a_share(symbol):
    return symbol.endswith((".SH", ".SZ", ".BJ"))

def fetch_a_share_data(symbol, period="6mo"):
    """Fetch A-share data. Uses yfinance as primary source."""
    import hashlib, time
    ck = hashlib.md5((symbol+period).encode()).hexdigest()
    if ck in _ashare_cache:
        cached_data, cached_time = _ashare_cache[ck]
        if time.time() - cached_time < 3600:
            return cached_data.copy()
    # Primary: Yahoo Finance (fast, works with proxy)
    try:
        import yfinance as yf
        yf_sym = symbol.replace(".SH", ".SS")  # Shanghai: .SH -> .SS
        t = yf.Ticker(yf_sym)
        df = t.history(period=period, auto_adjust=True)
        if df is not None and not df.empty:
            cols_ok = all(c in df.columns for c in ["Open","High","Low","Close","Volume"])
            if cols_ok:
                result = df[["Open","High","Low","Close","Volume"]]
                _ashare_cache[ck] = (result.copy(), time.time())
                return result
    except Exception:
        pass

    # Fallback: AkShare (requires direct China network access)
    try:
        import akshare as ak
        code = symbol.replace(".SH","").replace(".SZ","").replace(".BJ","")
        days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}.get(period, 180)
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now()-timedelta(days=days)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
        if df is not None and not df.empty:
            df = df.rename(columns={"日期":"Date","开盘":"Open","收盘":"Close","最高":"High","最低":"Low","成交量":"Volume"})
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")[["Open","High","Low","Close","Volume"]]
            _ashare_cache[ck] = (df.copy(), time.time())
            return df
    except Exception:
        pass

    return pd.DataFrame()

def compare_stocks(symbols, period="6mo"):
    data = {}
    for s in symbols:
        if is_a_share(s):
            df = fetch_a_share_data(s, period)
        else:
            from data_fetcher import fetch_stock_data
            df = fetch_stock_data(s, period=period)
        if df is not None and not df.empty and df["Close"].iloc[0] > 0:
            data[s] = df["Close"] / df["Close"].iloc[0] * 100
    return pd.DataFrame(data) if data else pd.DataFrame()